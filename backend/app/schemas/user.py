from pydantic import BaseModel, EmailStr
from datetime import datetime
import uuid


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    is_email_verified: bool
    created_at: datetime
    wallet_address: str | None = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None


class WalletResponse(BaseModel):
    address: str
    chain_id: int
    derivation_path: str


class ExportKeyRequest(BaseModel):
    password: str
