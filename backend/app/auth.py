from __future__ import annotations

import uuid
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, WebSocket, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass
class AuthInfo:
    user_id: str
    username: str
    role: str
    display_name: str
    scopes: list[str]


@dataclass(frozen=True)
class RoleDefinition:
    key: str
    label: str
    description: str
    scopes: tuple[str, ...]


RBAC_ROLE_DEFINITIONS: tuple[RoleDefinition, ...] = (
    RoleDefinition(
        key='radiologist',
        label='影像技师',
        description='可上传影像并查看分析结果。',
        scopes=('read:images', 'upload:images'),
    ),
    RoleDefinition(
        key='doctor',
        label='审核医生',
        description='可查看影像并提交审核意见。',
        scopes=('read:images', 'review:reports'),
    ),
    RoleDefinition(
        key='chief_doctor',
        label='主任医生',
        description='拥有全部权限：上传影像、查看分析、审核报告、正式确认。',
        scopes=('read:images', 'upload:images', 'review:reports', 'finalize:reports'),
    ),
)

SCOPE_TO_ROLE: dict[str, str] = {}
for role_def in RBAC_ROLE_DEFINITIONS:
    for scope in role_def.scopes:
        SCOPE_TO_ROLE.setdefault(scope, role_def.key)

ROLE_SCOPES: dict[str, tuple[str, ...]] = {r.key: r.scopes for r in RBAC_ROLE_DEFINITIONS}


def get_scopes_for_role(role: str) -> list[str]:
    return list(ROLE_SCOPES.get(role, ()))


RBAC_MENU_ITEMS: tuple[dict[str, Any], ...] = (
    {
        'key': 'upload',
        'label': '影像上传',
        'description': '上传新的影像文件并触发 AI 分析。',
        'required_scopes': ['upload:images'],
    },
    {
        'key': 'records',
        'label': '分析记录',
        'description': '查看影像列表、详情与预览。',
        'required_scopes': ['read:images'],
    },
    {
        'key': 'patients',
        'label': '患者档案',
        'description': '查询患者档案、病例统计与历史影像。',
        'required_scopes': ['read:images'],
    },
    {
        'key': 'datasets',
        'label': '数据集中心',
        'description': '维护公开牙科影像数据集、许可与适用任务。',
        'required_scopes': ['read:images'],
    },
    {
        'key': 'review',
        'label': '报告审核',
        'description': '提交医生审核意见并在有权限时正式确认。',
        'required_scopes': ['review:reports'],
    },
    {
        'key': 'access',
        'label': '权限说明',
        'description': '查看当前角色、权限与系统 RBAC 模型。',
        'required_scopes': [],
    },
    {
        'key': 'audit',
        'label': '审计日志',
        'description': '查看上传、审核、确认和分析完成等关键留痕事件。',
        'required_scopes': ['review:reports'],
    },
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, username: str, role: str, display_name: str) -> str:
    scopes = get_scopes_for_role(role)
    now = datetime.now(timezone.utc)
    payload = {
        'sub': user_id,
        'username': username,
        'role': role,
        'display_name': display_name or username,
        'scopes': scopes,
        'iat': now,
        'exp': now + timedelta(minutes=JWT_EXPIRE_MINUTES),
        'jti': str(uuid.uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token has expired')
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Invalid token: {exc}')
    return payload


def create_auth_info(payload: dict[str, Any]) -> AuthInfo:
    return AuthInfo(
        user_id=payload.get('sub', ''),
        username=payload.get('username', ''),
        role=payload.get('role', 'radiologist'),
        display_name=payload.get('display_name', ''),
        scopes=payload.get('scopes', []),
    )


def build_auth_profile(auth: AuthInfo) -> dict[str, Any]:
    role_def = next((r for r in RBAC_ROLE_DEFINITIONS if r.key == auth.role), None)
    role_label = role_def.label if role_def else auth.role

    menu_items: list[dict[str, Any]] = []
    for item in RBAC_MENU_ITEMS:
        required_scopes = item['required_scopes']
        menu_items.append({
            **item,
            'visible': all(scope in auth.scopes for scope in required_scopes),
        })

    return {
        'user_id': auth.user_id,
        'username': auth.username,
        'display_name': auth.display_name,
        'role': auth.role,
        'role_label': role_label,
        'permissions': auth.scopes,
        'roles': [auth.role],
        'menus': menu_items,
    }


def build_rbac_model_payload() -> dict[str, Any]:
    return {
        'permissions': [
            {'key': 'read:images', 'label': '查看影像', 'description': '允许查看影像记录、详情、影像预览与进度事件。'},
            {'key': 'upload:images', 'label': '上传影像', 'description': '允许上传新影像并触发 AI 分析任务。'},
            {'key': 'review:reports', 'label': '审核报告', 'description': '允许提交医生审核意见。'},
            {'key': 'finalize:reports', 'label': '正式确认', 'description': '允许将审核后的报告正式确认。'},
        ],
        'roles': [asdict(role) for role in RBAC_ROLE_DEFINITIONS],
        'menus': list(RBAC_MENU_ITEMS),
    }


def ensure_scopes(auth: AuthInfo, required_scopes: tuple[str, ...]) -> None:
    missing = [scope for scope in required_scopes if scope not in auth.scopes]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'Missing required scopes: {", ".join(missing)}',
        )


security = HTTPBearer(auto_error=False)


def require_api_auth(*required_scopes: str):
    async def dependency(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> AuthInfo:
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authorization header is missing')
        payload = decode_access_token(credentials.credentials)
        auth = create_auth_info(payload)
        ensure_scopes(auth, required_scopes)
        return auth

    return dependency


async def authorize_websocket(websocket: WebSocket, *required_scopes: str) -> AuthInfo:
    token = websocket.query_params.get('access_token')
    if not token:
        await websocket.close(code=4401)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing websocket access token')
    try:
        payload = decode_access_token(token)
    except HTTPException:
        await websocket.close(code=4403)
        raise
    auth = create_auth_info(payload)
    ensure_scopes(auth, required_scopes)
    return auth


def seed_default_users(db: Session) -> None:
    from app.models import UserRecord

    existing = db.scalar(select(UserRecord.user_id).limit(1))
    if existing is not None:
        return

    default_users = [
        UserRecord(
            username='admin',
            password_hash=hash_password('admin123'),
            role='chief_doctor',
            display_name='主任医生',
        ),
        UserRecord(
            username='doctor',
            password_hash=hash_password('doctor123'),
            role='doctor',
            display_name='审核医生',
        ),
        UserRecord(
            username='tech',
            password_hash=hash_password('tech123'),
            role='radiologist',
            display_name='影像技师',
        ),
    ]
    db.add_all(default_users)
    db.commit()
