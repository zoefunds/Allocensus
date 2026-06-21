from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func
from app.models.user import User, UserRole
from app.models.portfolio import Portfolio
from app.models.rebalancing import RebalancingProposal
from app.dependencies import AdminUser, DB
from app.models.audit import AuditEventType
from app.services.audit_service import log_event

router = APIRouter()


@router.get("/stats")
async def get_stats(admin: AdminUser, db: DB):
    users_count = await db.scalar(select(func.count()).select_from(User))
    portfolios_count = await db.scalar(select(func.count()).select_from(Portfolio))
    proposals_count = await db.scalar(select(func.count()).select_from(RebalancingProposal))
    return {
        "total_users": users_count,
        "total_portfolios": portfolios_count,
        "total_proposals": proposals_count,
    }


@router.get("/users")
async def list_users(admin: AdminUser, db: DB, limit: int = 50, offset: int = 0):
    result = await db.execute(select(User).limit(limit).offset(offset).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [{"id": str(u.id), "email": u.email, "full_name": u.full_name, "role": u.role.value, "is_active": u.is_active, "created_at": u.created_at.isoformat()} for u in users]


@router.patch("/users/{user_id}/role")
async def update_user_role(user_id: str, role: str, admin: AdminUser, db: DB):
    try:
        new_role = UserRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
    import uuid
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = new_role
    await log_event(db, AuditEventType.ADMIN_ACTION, user_id=admin.id, resource_id=user_id, metadata={"action": "role_change", "new_role": role})
    return {"message": f"Role updated to {role}"}


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(user_id: str, admin: AdminUser, db: DB):
    import uuid
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await log_event(db, AuditEventType.ADMIN_ACTION, user_id=admin.id, resource_id=user_id, metadata={"action": "deactivate"})
    return {"message": "User deactivated"}
