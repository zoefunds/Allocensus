from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.user import UserUpdate, UserResponse
from app.dependencies import CurrentUser, DB
from app.utils.security import decrypt_private_key, verify_password
from pydantic import BaseModel
import json

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUser):
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(req: UserUpdate, user: CurrentUser, db: DB):
    if req.full_name is not None:
        user.full_name = req.full_name
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/me/wallet")
async def get_wallet(user: CurrentUser, db: DB):
    result = await db.execute(
        select(Wallet)
        .options(selectinload(Wallet.keystore))
        .where(Wallet.user_id == user.id)
    )
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    keystore_json = None
    if wallet.keystore and wallet.keystore.encrypted_private_key:
        stored = wallet.keystore.encrypted_private_key
        if isinstance(stored, str) and stored.strip().startswith("{"):
            keystore_json = stored
        elif isinstance(stored, dict):
            keystore_json = json.dumps(stored)

    return {
        "address":      wallet.address,
        "chain":        wallet.chain,
        "keystore_json": keystore_json,
        "created_at":   wallet.created_at.isoformat(),
    }


class ExportKeyRequest(BaseModel):
    password: str


@router.post("/me/wallet/export-key")
async def export_private_key(req: ExportKeyRequest, user: CurrentUser, db: DB):
    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    result = await db.execute(
        select(Wallet)
        .options(selectinload(Wallet.keystore))
        .where(Wallet.user_id == user.id)
    )
    wallet = result.scalar_one_or_none()
    if not wallet or not wallet.keystore:
        raise HTTPException(status_code=404, detail="Wallet not found")

    private_key = decrypt_private_key(
        wallet.keystore.encrypted_private_key,
        user.hashed_password,
    )
    return {"private_key": private_key, "address": wallet.address}
