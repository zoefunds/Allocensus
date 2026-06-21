from app.workers.celery_app import celery_app
import asyncio
import structlog

log = structlog.get_logger()


@celery_app.task(bind=True, max_retries=10, default_retry_delay=10)
def poll_genlayer_result(self, proposal_id: str, tx_hash: str, user_email: str):
    """Background task: poll Genlayer until tx is confirmed, then save rationale."""
    from app.services.genlayer_service import genlayer_service
    from app.database import AsyncSessionLocal
    from app.models.rebalancing import RebalancingProposal, ProposalStatus
    from app.services.rebalancing_service import process_rationale_result
    from sqlalchemy import select
    import uuid

    async def _run():
        raw = await genlayer_service.read_rationale(tx_hash)
        if not raw:
            raise Exception("Result not ready")
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(RebalancingProposal).where(RebalancingProposal.id == uuid.UUID(proposal_id))
            )
            proposal = result.scalar_one_or_none()
            if proposal and proposal.status == ProposalStatus.PENDING_CONSENSUS:
                await process_rationale_result(proposal, raw, user_email, db)
                await db.commit()
                log.info("rationale_saved", proposal_id=proposal_id)

    try:
        asyncio.run(_run())
    except Exception as exc:
        log.warning("poll_retry", proposal_id=proposal_id, attempt=self.request.retries)
        raise self.retry(exc=exc)
