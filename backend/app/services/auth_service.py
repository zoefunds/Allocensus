from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.user import User, UserRole
from app.models.wallet import Wallet
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.utils.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    generate_secure_token,
)
from app.services.wallet_service import create_wallet_for_user
from app.services.notification_service import send_verification_email
import uuid


async def register_user(req: RegisterRequest, db: AsyncSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    hashed = hash_password(req.password)
    verification_token = generate_secure_token()

    user = User(
        email=req.email,
        hashed_password=hashed,
        full_name=req.full_name,
        role=UserRole.PORTFOLIO_MANAGER,
        email_verification_token=verification_token,
    )
    db.add(user)
    await db.flush()

    wallet = await create_wallet_for_user(user, hashed, db, plain_password=req.password)
    await db.flush()

    await send_verification_email(user.email, verification_token)

    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=str(user.id),
        role=user.role.value,
        wallet_address=wallet.address,
    )


async def login_user(req: LoginRequest, db: AsyncSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    wallet_result = await db.execute(select(Wallet).where(Wallet.user_id == user.id))
    wallet = wallet_result.scalar_one_or_none()

    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=str(user.id),
        role=user.role.value,
        wallet_address=wallet.address if wallet else None,
    )
