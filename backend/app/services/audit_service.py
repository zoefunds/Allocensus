from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditEvent, AuditEventType, ComplianceLog
from app.models.rebalancing import RebalancingProposal
import uuid
import structlog

log = structlog.get_logger()


async def log_event(
    db: AsyncSession,
    event_type: AuditEventType,
    user_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict | None = None,
    on_chain_ref: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        user_id=user_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        event_metadata=metadata or {},
        on_chain_ref=on_chain_ref,
    )
    db.add(event)
    log.info("audit_event", type=event_type.value, user_id=str(user_id), resource=resource_id)
    return event


async def log_compliance(
    db: AsyncSession,
    check_type: str,
    passed: bool,
    portfolio_id: uuid.UUID | None = None,
    proposal_id: uuid.UUID | None = None,
    details: dict | None = None,
) -> ComplianceLog:
    entry = ComplianceLog(
        portfolio_id=portfolio_id,
        proposal_id=proposal_id,
        check_type=check_type,
        passed=passed,
        details=details or {},
    )
    db.add(entry)
    return entry
