from datetime import datetime, timedelta, timezone
from typing import Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import os
import base64
import secrets
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict[str, Any]) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload["type"] = "access"
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload["type"] = "refresh"
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_access_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def verify_refresh_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None


def _derive_encryption_key(user_password_hash: str, salt: bytes) -> bytes:
    """Derive a 32-byte AES key from user credential using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=settings.WALLET_PBKDF2_ITERATIONS,
    )
    return kdf.derive(user_password_hash.encode())


def encrypt_private_key(private_key_hex: str, user_password_hash: str) -> str:
    """Encrypt wallet private key with AES-256-GCM. Returns base64-encoded payload."""
    salt = os.urandom(16)
    key = _derive_encryption_key(user_password_hash, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, private_key_hex.encode(), None)
    payload = salt + nonce + ciphertext
    return base64.b64encode(payload).decode()


def decrypt_private_key(encrypted_b64: str, user_password_hash: str) -> str:
    """Decrypt wallet private key. Raises ValueError on wrong password."""
    try:
        payload = base64.b64decode(encrypted_b64)
        salt = payload[:16]
        nonce = payload[16:28]
        ciphertext = payload[28:]
        key = _derive_encryption_key(user_password_hash, salt)
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()
    except Exception as e:
        raise ValueError("Failed to decrypt private key — wrong password or corrupted data") from e


def generate_secure_token(n_bytes: int = 32) -> str:
    return secrets.token_urlsafe(n_bytes)
