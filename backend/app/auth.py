from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import jwt
from fastapi import Depends, HTTPException, WebSocket, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.config import LOGTO_API_RESOURCE, LOGTO_ISSUER, LOGTO_JWKS_URI


@dataclass
class AuthInfo:
    sub: str
    client_id: str | None
    organization_id: str | None
    scopes: list[str]
    audience: list[str]
    effective_roles: list[str]


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
        description='可查看影像、审核并正式确认报告。',
        scopes=('read:images', 'review:reports', 'finalize:reports'),
    ),
)


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
)


security = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def get_jwks_client() -> PyJWKClient:
    return PyJWKClient(LOGTO_JWKS_URI)


def normalize_audience(aud: Any) -> list[str]:
    if isinstance(aud, str):
        return [aud]
    if isinstance(aud, list):
        return [str(item) for item in aud]
    return []


def infer_roles_from_scopes(scopes: list[str]) -> list[str]:
    scope_set = set(scopes)
    matched_roles = [role for role in RBAC_ROLE_DEFINITIONS if set(role.scopes).issubset(scope_set)]
    effective_roles: list[RoleDefinition] = []

    for role in matched_roles:
        role_scope_set = set(role.scopes)
        if any(role_scope_set < set(candidate.scopes) for candidate in matched_roles):
            continue
        effective_roles.append(role)

    return [role.key for role in effective_roles]


def validate_jwt(token: str) -> dict[str, Any]:
    signing_key = get_jwks_client().get_signing_key_from_jwt(token)
    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=['RS256'],
        issuer=LOGTO_ISSUER,
        options={'verify_aud': False},
    )
    audience = normalize_audience(payload.get('aud'))
    if LOGTO_API_RESOURCE not in audience:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Token audience is invalid')
    return payload


def create_auth_info(payload: dict[str, Any]) -> AuthInfo:
    scope_value = payload.get('scope', '')
    scopes = [item for item in scope_value.split(' ') if item]
    return AuthInfo(
        sub=payload.get('sub', ''),
        client_id=payload.get('client_id'),
        organization_id=payload.get('organization_id'),
        scopes=scopes,
        audience=normalize_audience(payload.get('aud')),
        effective_roles=infer_roles_from_scopes(scopes),
    )


def build_auth_profile(auth: AuthInfo) -> dict[str, Any]:
    menu_items: list[dict[str, Any]] = []
    for item in RBAC_MENU_ITEMS:
        required_scopes = item['required_scopes']
        menu_items.append(
            {
                **item,
                'visible': all(scope in auth.scopes for scope in required_scopes),
            }
        )

    return {
        'sub': auth.sub,
        'client_id': auth.client_id,
        'organization_id': auth.organization_id,
        'permissions': auth.scopes,
        'roles': auth.effective_roles,
        'audience': auth.audience,
        'menus': menu_items,
    }


def build_rbac_model_payload() -> dict[str, Any]:
    return {
        'resource': LOGTO_API_RESOURCE,
        'permissions': [
            {
                'key': 'read:images',
                'label': '查看影像',
                'description': '允许查看影像记录、详情、影像预览与进度事件。',
            },
            {
                'key': 'upload:images',
                'label': '上传影像',
                'description': '允许上传新影像并触发 AI 分析任务。',
            },
            {
                'key': 'review:reports',
                'label': '审核报告',
                'description': '允许提交医生审核意见。',
            },
            {
                'key': 'finalize:reports',
                'label': '正式确认',
                'description': '允许将审核后的报告正式确认。',
            },
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


def require_api_auth(*required_scopes: str):
    async def dependency(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> AuthInfo:
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authorization header is missing')
        try:
            payload = validate_jwt(credentials.credentials)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Invalid access token: {exc}') from exc
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
        payload = validate_jwt(token)
    except HTTPException:
        await websocket.close(code=4403)
        raise
    except Exception as exc:  # noqa: BLE001
        await websocket.close(code=4401)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Invalid access token: {exc}') from exc
    auth = create_auth_info(payload)
    ensure_scopes(auth, required_scopes)
    return auth
