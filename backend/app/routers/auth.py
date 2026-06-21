from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshRequest, PasswordChangeRequest, PasswordResetRequest, PasswordResetConfirm,
)
from app.services.auth_service import register_user, login_user
from app.services.notification_service import send_verification_email
from app.utils.security import (
    verify_refresh_token, create_access_token, create_refresh_token,
    verify_password, hash_password, generate_secure_token,
)
from app.models.user import User
from app.models.audit import AuditEventType
from app.services.audit_service import log_event
from app.dependencies import CurrentUser, DB

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(req: RegisterRequest, db: DB):
    return await register_user(req, db)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, request: Request, db: DB):
    result = await login_user(req, db)
    await log_event(
        db, AuditEventType.USER_LOGIN,
        user_id=None,
        ip_address=request.client.host if request.client else None,
        metadata={"email": req.email},  # type: ignore[call-arg]
    )
    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, db: DB):
    payload = verify_refresh_token(req.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = payload["sub"]
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return TokenResponse(
        access_token=create_access_token({"sub": str(user.id), "role": user.role.value}),
        refresh_token=create_refresh_token({"sub": str(user.id)}),
        user_id=str(user.id),
        role=user.role.value,
    )


@router.post("/verify-email")
async def verify_email(token: str, db: DB):
    result = await db.execute(select(User).where(User.email_verification_token == token))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    user.is_email_verified = True
    user.email_verification_token = None
    return {"message": "Email verified successfully"}


@router.post("/forgot-password")
async def forgot_password(req: PasswordResetRequest, db: DB):
    result = await db.execute(select(User).where(User.email == req.email, User.is_active == True))
    user = result.scalar_one_or_none()
    if user:
        token = generate_secure_token()
        user.password_reset_token = token
        await db.flush()
        try:
            from app.services.notification_service import _send
            reset_url = f"https://allocensus.vercel.app/reset-password?token={token}"
            await _send(
                subject="Reset your Allocensus password",
                to_email=user.email,
                html=f"""
                <div style="font-family:sans-serif;max-width:480px;margin:auto">
                  <h2 style="color:#10b981">Reset your password</h2>
                  <p>Click the link below to reset your Allocensus password. This link expires in 1 hour.</p>
                  <a href="{reset_url}" style="display:inline-block;background:#10b981;color:#000;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;margin:16px 0">
                    Reset Password
                  </a>
                  <p style="color:#666;font-size:13px">If you didn't request this, ignore this email.</p>
                </div>"""
            )
        except Exception:
            pass
    # Always return 200 — don't reveal whether email exists
    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(req: PasswordResetConfirm, db: DB):
    result = await db.execute(select(User).where(User.password_reset_token == req.token))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user.hashed_password = hash_password(req.new_password)
    user.password_reset_token = None
    return {"message": "Password has been reset. You can now log in."}


@router.post("/change-password")
async def change_password(req: PasswordChangeRequest, user: CurrentUser, db: DB):
    if not verify_password(req.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.hashed_password = hash_password(req.new_password)
    await log_event(db, AuditEventType.PASSWORD_CHANGE, user_id=user.id)
    return {"message": "Password updated"}
