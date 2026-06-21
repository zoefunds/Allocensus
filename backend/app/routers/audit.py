from fastapi import APIRouter, Query
from sqlalchemy import select
from app.models.audit import AuditEvent, ComplianceLog
from app.dependencies import CurrentUser, DB
from datetime import datetime
from typing import Optional, List

router = APIRouter()


@router.get("/events")
async def get_audit_events(
    user: CurrentUser,
    db: DB,
    limit: int = Query(50, le=200),
    offset: int = 0,
    event_type: Optional[str] = None,
):
    query = select(AuditEvent).where(AuditEvent.user_id == user.id).order_by(AuditEvent.created_at.desc()).limit(limit).offset(offset)
    if event_type:
        from app.models.audit import AuditEventType
        query = query.where(AuditEvent.event_type == event_type)
    result = await db.execute(query)
    events = result.scalars().all()
    return [
        {
            "id": str(e.id),
            "event_type": e.event_type.value,
            "resource_type": e.resource_type,
            "resource_id": e.resource_id,
            "ip_address": e.ip_address,
            "on_chain_ref": e.on_chain_ref,
            "metadata": e.metadata,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


@router.get("/compliance")
async def get_compliance_logs(user: CurrentUser, db: DB, limit: int = 50):
    result = await db.execute(
        select(ComplianceLog).order_by(ComplianceLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()
    return [{"id": str(l.id), "check_type": l.check_type, "passed": l.passed, "details": l.details, "created_at": l.created_at.isoformat()} for l in logs]
