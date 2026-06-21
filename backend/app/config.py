from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Allocensus"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    DATABASE_URL: str = "postgresql+asyncpg://allocensus:allocensus_dev@localhost:5432/allocensus"
    DATABASE_URL_SYNC: str = "postgresql://allocensus:allocensus_dev@localhost:5432/allocensus"

    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    WALLET_ENCRYPTION_KEY: str = "0" * 64
    WALLET_PBKDF2_ITERATIONS: int = 310000

    GENLAYER_RPC_URL: str = "https://studio.genlayer.com/api"
    GENLAYER_CONTRACT_ADDRESS: str = "0xe45A5379bDD30BF75D08752cb32c4178f59445EA"

    COINGECKO_API_KEY: str = ""
    YAHOO_FINANCE_ENABLED: bool = True

    BREVO_API_KEY: str = ""
    EMAIL_FROM: str = "preciousmofeoluwa@gmail.com"
    EMAIL_FROM_NAME: str = "Allocensus"

    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "allocensus-reports"
    R2_PUBLIC_URL: str = ""

    SENTRY_DSN: Optional[str] = None

    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 20

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
