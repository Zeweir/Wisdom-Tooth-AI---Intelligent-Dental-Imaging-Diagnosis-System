from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import AuthInfo
from app.models import AuditLogRecord


def create_audit_log(
    db: Session,
    *,
    actor_sub: str,
    actor_client_id: str | None,
    actor_organization_id: str | None,
    actor_roles: list[str],
    action: str,
    resource_type: str,
    resource_id: str,
    detail: dict[str, Any],
) -> AuditLogRecord:
    audit_log = AuditLogRecord(
        actor_sub=actor_sub,
        actor_client_id=actor_client_id,
        actor_organization_id=actor_organization_id,
        actor_roles=actor_roles,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
    )
    db.add(audit_log)
    return audit_log


def create_user_audit_log(
    db: Session,
    *,
    auth: AuthInfo,
    action: str,
    resource_type: str,
    resource_id: str,
    detail: dict[str, Any],
) -> AuditLogRecord:
    return create_audit_log(
        db,
        actor_sub=auth.sub,
        actor_client_id=auth.client_id,
        actor_organization_id=auth.organization_id,
        actor_roles=auth.effective_roles,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
    )


def create_system_audit_log(
    db: Session,
    *,
    action: str,
    resource_type: str,
    resource_id: str,
    detail: dict[str, Any],
) -> AuditLogRecord:
    return create_audit_log(
        db,
        actor_sub='system:celery',
        actor_client_id='celery-worker',
        actor_organization_id=None,
        actor_roles=['system'],
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
    )


def serialize_audit_log(audit_log: AuditLogRecord) -> dict[str, Any]:
    return {
        'audit_log_id': audit_log.audit_log_id,
        'actor_sub': audit_log.actor_sub,
        'actor_client_id': audit_log.actor_client_id,
        'actor_organization_id': audit_log.actor_organization_id,
        'actor_roles': audit_log.actor_roles,
        'action': audit_log.action,
        'resource_type': audit_log.resource_type,
        'resource_id': audit_log.resource_id,
        'detail': audit_log.detail,
        'created_at': audit_log.created_at.isoformat(),
    }


def list_audit_logs(
    db: Session,
    *,
    limit: int = 50,
    action: str | None = None,
    resource_type: str | None = None,
) -> list[AuditLogRecord]:
    statement = select(AuditLogRecord).order_by(AuditLogRecord.created_at.desc()).limit(limit)
    if action:
        statement = statement.where(AuditLogRecord.action == action)
    if resource_type:
        statement = statement.where(AuditLogRecord.resource_type == resource_type)
    return db.execute(statement).scalars().all()
