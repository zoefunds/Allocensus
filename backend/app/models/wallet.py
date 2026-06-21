import uuid
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base, TimestampMixin


class Wallet(Base, TimestampMixin):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    address: Mapped[str] = mapped_column(String(42), unique=True, nullable=False, index=True)
    derivation_path: Mapped[str] = mapped_column(String(64), nullable=False, default="m/44'/60'/0'/0/0")
    chain_id: Mapped[int] = mapped_column(nullable=False, default=61999)  # StudioNet chain ID

    user: Mapped["User"] = relationship("User", back_populates="wallet")
    keystore: Mapped["EncryptedKeystore | None"] = relationship("EncryptedKeystore", back_populates="wallet", uselist=False)


class EncryptedKeystore(Base, TimestampMixin):
    __tablename__ = "encrypted_keystores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), unique=True, nullable=False)
    encrypted_private_key: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_mnemonic: Mapped[str | None] = mapped_column(Text, nullable=True)

    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="keystore")
