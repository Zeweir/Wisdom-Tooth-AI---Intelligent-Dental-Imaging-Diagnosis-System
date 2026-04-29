from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from urllib.parse import urlsplit

import jwt
from fastapi import Depends, HTTPException, WebSocket, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.config import LOGTO_API_RESOURCE, LOGTO_ISSUER, LOGTO_JWKS_URI, LOGTO_REQUIRE_ROLE_CLAIM, LOGTO_ROLE_CLAIM_NAMES


@dataclass
class AuthInfo:
    sub: str
    client_id: str | None
    organization_id: str | None
    scopes: list[str]
    audience: list[str]
    inferred_roles: list[str]
    token_roles: list[str]
    effective_roles: list[str]
    role_source: str
    role_claim_keys: list[str]
    token_claim_keys: list[str]
    claim_preview: dict[str, Any]


ROLE_CLAIM_CANDIDATES: tuple[str, ...] = (
    *dict.fromkeys([
        *LOGTO_ROLE_CLAIM_NAMES,
        'roles',
        'role_names',
        'roleNames',
        'urn:logto:roles',
    ]),
)

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


def expand_scopes_from_roles(scopes: list[str], roles: list[str]) -> list[str]:
    expanded = list(dict.fromkeys(scopes))
    role_scope_map = {role.key: role.scopes for role in RBAC_ROLE_DEFINITIONS}
    for role in roles:
        for scope in role_scope_map.get(role, ()):
            if scope not in expanded:
                expanded.append(scope)
    return expanded


def normalize_string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        items = [item.strip() for item in value.replace(',', ' ').split(' ')]
        return [item for item in items if item]
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def extract_token_roles(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    role_claim_keys: list[str] = []
    token_roles: list[str] = []

    for claim_key, claim_value in payload.items():
        normalized_key = claim_key.lower()
        is_candidate = claim_key in ROLE_CLAIM_CANDIDATES or normalized_key.endswith(':roles') or normalized_key.endswith('/roles')
        if not is_candidate:
            continue

        normalized_roles = normalize_string_list(claim_value)
        if not normalized_roles:
            continue

        role_claim_keys.append(claim_key)
        for role in normalized_roles:
            if role not in token_roles:
                token_roles.append(role)

    return token_roles, role_claim_keys


def build_claim_preview(payload: dict[str, Any], role_claim_keys: list[str]) -> dict[str, Any]:
    preview_keys = ['sub', 'aud', 'scope', 'client_id', 'organization_id', *role_claim_keys]
    preview: dict[str, Any] = {}
    for key in preview_keys:
        if key in payload:
            preview[key] = payload[key]
    return preview


def get_role_claim_alignment_status(auth: AuthInfo) -> str:
    if auth.token_roles:
        return 'aligned'
    if auth.inferred_roles and LOGTO_REQUIRE_ROLE_CLAIM:
        return 'claim_required_missing'
    if auth.inferred_roles:
        return 'fallback_scope_inference'
    return 'missing'


def build_logto_custom_jwt_script() -> str:
    claim_key = LOGTO_ROLE_CLAIM_NAMES[0] if LOGTO_ROLE_CLAIM_NAMES else 'urn:logto:roles'
    return '\n'.join(
        [
            'const getCustomJwtClaims = async ({ token, context, environmentVariables }) => {',
            '  const roleNames = Array.isArray(context?.user?.roles)',
            "    ? context.user.roles.map((role) => typeof role === 'string' ? role : role?.name).filter(Boolean)",
            '    : [];',
            f"  return {{ '{claim_key}': roleNames }};",
            '};',
        ]
    )


def is_equivalent_loopback_issuer(actual_issuer: str, expected_issuer: str) -> bool:
    actual = urlsplit(actual_issuer)
    expected = urlsplit(expected_issuer)
    loopback_hosts = {'127.0.0.1', 'localhost'}
    return (
        actual.scheme == expected.scheme
        and actual.hostname in loopback_hosts
        and expected.hostname in loopback_hosts
        and actual.port == expected.port
        and actual.path.rstrip('/') == expected.path.rstrip('/')
    )


def ensure_valid_issuer(payload: dict[str, Any]) -> None:
    issuer = str(payload.get('iss', ''))
    if issuer == LOGTO_ISSUER:
        return
    if issuer and is_equivalent_loopback_issuer(issuer, LOGTO_ISSUER):
        return
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid access token: Invalid issuer')


def validate_jwt(token: str) -> dict[str, Any]:
    header = jwt.get_unverified_header(token)
    algorithm = header.get('alg')
    if not algorithm or str(algorithm).lower() == 'none':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid access token: missing or unsafe alg header')
    signing_key = get_jwks_client().get_signing_key_from_jwt(token)
    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=[str(algorithm)],
        options={'verify_aud': False, 'verify_iss': False},
    )
    ensure_valid_issuer(payload)
    audience = normalize_audience(payload.get('aud'))
    if LOGTO_API_RESOURCE not in audience:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Token audience is invalid')
    return payload


def create_auth_info(payload: dict[str, Any]) -> AuthInfo:
    scope_value = payload.get('scope', '')
    raw_scopes = [item for item in scope_value.split(' ') if item]
    token_roles, role_claim_keys = extract_token_roles(payload)
    scopes = expand_scopes_from_roles(raw_scopes, token_roles)
    inferred_roles = infer_roles_from_scopes(scopes)
    effective_roles = token_roles or inferred_roles
    return AuthInfo(
        sub=payload.get('sub', ''),
        client_id=payload.get('client_id'),
        organization_id=payload.get('organization_id'),
        scopes=scopes,
        audience=normalize_audience(payload.get('aud')),
        inferred_roles=inferred_roles,
        token_roles=token_roles,
        effective_roles=effective_roles,
        role_source='token_claim' if token_roles else 'scope_inference' if inferred_roles else 'none',
        role_claim_keys=role_claim_keys,
        token_claim_keys=sorted(payload.keys()),
        claim_preview=build_claim_preview(payload, role_claim_keys),
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
        'inferred_roles': auth.inferred_roles,
        'token_roles': auth.token_roles,
        'roles': auth.effective_roles,
        'role_source': auth.role_source,
        'role_claim_keys': auth.role_claim_keys,
        'configured_role_claim_names': list(LOGTO_ROLE_CLAIM_NAMES),
        'role_claim_required': LOGTO_REQUIRE_ROLE_CLAIM,
        'role_claim_alignment_status': get_role_claim_alignment_status(auth),
        'audience': auth.audience,
        'token_claim_keys': auth.token_claim_keys,
        'claim_preview': auth.claim_preview,
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
        'role_resolution': {
            'preferred_source': 'token_claim',
            'fallback_source': 'scope_inference',
            'token_role_claim_candidates': list(ROLE_CLAIM_CANDIDATES),
            'description': '若 access token 中存在可识别的角色 claim，则优先使用该角色列表；否则根据已授予 scopes 推断匹配角色。',
        },
        'logto_claim_setup': {
            'configured_claim_names': list(LOGTO_ROLE_CLAIM_NAMES),
            'role_claim_required': LOGTO_REQUIRE_ROLE_CLAIM,
            'custom_jwt_function_name': 'getCustomJwtClaims',
            'custom_jwt_function_signature': 'const getCustomJwtClaims = async ({ token, context, environmentVariables }) => ({})',
            'recommended_script': build_logto_custom_jwt_script(),
        },
    }


def ensure_scopes(auth: AuthInfo, required_scopes: tuple[str, ...]) -> None:
    missing = [scope for scope in required_scopes if scope not in auth.scopes]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'Missing required scopes: {", ".join(missing)}',
        )


def ensure_role_claim_alignment(auth: AuthInfo) -> None:
    if LOGTO_REQUIRE_ROLE_CLAIM and not auth.token_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'Token role claim is required. Expected one of: {", ".join(LOGTO_ROLE_CLAIM_NAMES)}',
        )


def require_api_auth(*required_scopes: str, enforce_role_claim: bool = True):
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
        if enforce_role_claim:
            ensure_role_claim_alignment(auth)
        ensure_scopes(auth, required_scopes)
        return auth

    return dependency


async def authorize_websocket(websocket: WebSocket, *required_scopes: str, enforce_role_claim: bool = True) -> AuthInfo:
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
    if enforce_role_claim:
        ensure_role_claim_alignment(auth)
    ensure_scopes(auth, required_scopes)
    return auth
