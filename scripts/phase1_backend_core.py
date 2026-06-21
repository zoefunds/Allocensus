"""
ALLOCENSUS — Phase 1 Backend Core
Creates: main.py, config.py, database.py, dependencies.py
"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  FILE {path}")

print("\n[1/4] Writing app core files...")

write("backend/app/__init__.py", "")

write("backend/app/config.py", '''\
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    APP_NAME: str = "Allocensus"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Wallet
    WALLET_ENCRYPTION_KEY: str
    WALLET_PBKDF2_ITERATIONS: int = 310000

    # Genlayer
    GENLAYER_RPC_URL: str = "https://studio.genlayer.com/api"
    GENLAYER_CONTRACT_ADDRESS: str = ""
    GENLAYER_DEPLOYER_PRIVATE_KEY: str = ""

    # Price feeds
    COINGECKO_API_KEY: str = ""
    YAHOO_FINANCE_ENABLED: bool = True

    # Email
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@allocensus.com"
    EMAIL_FROM_NAME: str = "Allocensus"

    # Storage
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "allocensus-reports"
    R2_PUBLIC_URL: str = ""

    # Monitoring
    SENTRY_DSN: str = ""

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 20

    @field_validator("DATABASE_URL_SYNC", mode="before")
    @classmethod
    def build_sync_url(cls, v: str, info) -> str:
        if v:
            return v
        db_url = info.data.get("DATABASE_URL", "")
        return db_url.replace("postgresql+asyncpg://", "postgresql://")

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
''')

write("backend/app/database.py", '''\
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func
from datetime import datetime
from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
''')

write("backend/app/dependencies.py", '''\
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.utils.security import verify_access_token
from app.models.user import User, UserRole
from typing import Annotated

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    token = credentials.credentials
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


async def require_portfolio_manager(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role not in (UserRole.ADMIN, UserRole.PORTFOLIO_MANAGER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Portfolio Manager access required")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]
PMUser = Annotated[User, Depends(require_portfolio_manager)]
DB = Annotated[AsyncSession, Depends(get_db)]
''')

write("backend/app/main.py", '''\
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.config import settings
from app.routers import auth, users, portfolios, rebalancing, audit, admin, health
from app.middleware.rate_limit import RateLimitMiddleware

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("allocensus_startup", env=settings.APP_ENV)
    yield
    log.info("allocensus_shutdown")


if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        traces_sample_rate=0.2,
        environment=settings.APP_ENV,
    )

app = FastAPI(
    title="Allocensus API",
    description="AI-Validated Portfolio Rebalancing Intelligence",
    version="1.0.0",
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url="/api/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

if settings.is_production:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*.railway.app", "*.allocensus.com"])

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(portfolios.router, prefix="/api/portfolios", tags=["Portfolios"])
app.include_router(rebalancing.router, prefix="/api/rebalancing", tags=["Rebalancing"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
''')

print("\n[2/4] Writing middleware...")

write("backend/app/middleware/__init__.py", "")

write("backend/app/middleware/rate_limit.py", '''\
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import redis.asyncio as aioredis
import time
from app.config import settings

_redis: aioredis.Redis | None = None

async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/auth"):
            limit = 10
        else:
            limit = settings.RATE_LIMIT_PER_MINUTE

        client_ip = request.client.host if request.client else "unknown"
        key = f"rl:{client_ip}:{int(time.time() // 60)}"

        try:
            r = await get_redis()
            count = await r.incr(key)
            if count == 1:
                await r.expire(key, 60)
            if count > limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again in a minute."},
                    headers={"Retry-After": "60"},
                )
        except Exception:
            pass  # degrade gracefully if Redis is unavailable

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        return response
''')

print("\n[3/4] Writing security utils...")

write("backend/app/utils/__init__.py", "")

write("backend/app/utils/security.py", '''\
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
''')

write("backend/app/utils/constraints.py", '''\
"""
Portfolio constraint engine — 8 hard rules enforced before any rebalancing
submission reaches the Genlayer contract.
"""
from dataclasses import dataclass
from typing import Dict, List

ILLIQUID_CLASSES = {"defi_protocols", "tokenised_rwa"}


@dataclass
class ConstraintViolation:
    rule: str
    message: str
    current_value: float
    limit: float


def validate_portfolio_constraints(
    allocations: Dict[str, float],
    asset_classes: Dict[str, str],
) -> List[ConstraintViolation]:
    """
    Validate allocation dict against hard portfolio rules.
    allocations: {asset_id: weight_pct}  (weights must sum to ~100)
    asset_classes: {asset_id: asset_class_name}
    Returns list of violations (empty = passes all constraints).
    """
    violations: List[ConstraintViolation] = []
    total = sum(allocations.values())

    # Rule 1 — weights must sum to ~100%
    if abs(total - 100.0) > 0.5:
        violations.append(ConstraintViolation(
            rule="WEIGHT_SUM",
            message=f"Allocations must sum to 100% (got {total:.2f}%)",
            current_value=total,
            limit=100.0,
        ))

    # Rule 2 — max single asset concentration 30%
    for asset_id, weight in allocations.items():
        if weight > 30.0:
            violations.append(ConstraintViolation(
                rule="MAX_SINGLE_ASSET",
                message=f"Asset '{asset_id}' exceeds 30% max concentration ({weight:.2f}%)",
                current_value=weight,
                limit=30.0,
            ))

    # Rule 3 — max single asset class 60%
    class_totals: Dict[str, float] = {}
    for asset_id, weight in allocations.items():
        cls = asset_classes.get(asset_id, "unknown")
        class_totals[cls] = class_totals.get(cls, 0.0) + weight
    for cls, total_weight in class_totals.items():
        if total_weight > 60.0:
            violations.append(ConstraintViolation(
                rule="MAX_ASSET_CLASS",
                message=f"Asset class '{cls}' exceeds 60% limit ({total_weight:.2f}%)",
                current_value=total_weight,
                limit=60.0,
            ))

    # Rule 4 — min liquidity reserve 5% (stablecoins / cash)
    liquid_weight = class_totals.get("stablecoins", 0.0) + class_totals.get("cash", 0.0)
    if liquid_weight < 5.0:
        violations.append(ConstraintViolation(
            rule="MIN_LIQUIDITY",
            message=f"Liquidity reserve below 5% minimum ({liquid_weight:.2f}%)",
            current_value=liquid_weight,
            limit=5.0,
        ))

    # Rule 5 — max illiquid allocation 25%
    illiquid_total = sum(class_totals.get(c, 0.0) for c in ILLIQUID_CLASSES)
    if illiquid_total > 25.0:
        violations.append(ConstraintViolation(
            rule="MAX_ILLIQUID",
            message=f"Illiquid allocation exceeds 25% ({illiquid_total:.2f}%)",
            current_value=illiquid_total,
            limit=25.0,
        ))

    # Rule 6 — min 3 asset classes
    active_classes = {cls for asset_id, cls in asset_classes.items() if allocations.get(asset_id, 0) > 0}
    if len(active_classes) < 3:
        violations.append(ConstraintViolation(
            rule="MIN_DIVERSIFICATION",
            message=f"Portfolio must span at least 3 asset classes (has {len(active_classes)})",
            current_value=float(len(active_classes)),
            limit=3.0,
        ))

    # Rule 7 — no leverage (negative weights)
    for asset_id, weight in allocations.items():
        if weight < 0:
            violations.append(ConstraintViolation(
                rule="NO_LEVERAGE",
                message=f"Asset '{asset_id}' has negative weight — leverage not permitted",
                current_value=weight,
                limit=0.0,
            ))

    # Rule 8 — max single DeFi protocol 15%
    for asset_id, weight in allocations.items():
        if asset_classes.get(asset_id) == "defi_protocols" and weight > 15.0:
            violations.append(ConstraintViolation(
                rule="MAX_DEFI_PROTOCOL",
                message=f"DeFi protocol '{asset_id}' exceeds 15% limit ({weight:.2f}%)",
                current_value=weight,
                limit=15.0,
            ))

    return violations
''')

print("\n[4/4] Writing health router...")

write("backend/app/routers/__init__.py", "")

write("backend/app/routers/health.py", '''\
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
import redis.asyncio as aioredis
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    db_ok = False
    redis_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
        redis_ok = True
    except Exception:
        pass
    return {
        "status": "ok" if db_ok and redis_ok else "degraded",
        "database": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
        "version": "1.0.0",
    }
''')

print("\n✅ Backend core complete.")
