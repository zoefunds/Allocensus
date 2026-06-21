from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
import structlog

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("allocensus_starting", env=settings.APP_ENV)
    yield
    log.info("allocensus_stopping")


app = FastAPI(
    title="Allocensus API",
    description="AI-Validated Portfolio Rebalancing Intelligence",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    sentry_sdk.init(dsn=settings.SENTRY_DSN, integrations=[FastApiIntegration()])

from app.routers import auth, users, portfolios, rebalancing, audit, admin, health
from app.routers.export import router as export_router

app.include_router(health.router,      prefix="/api/health",      tags=["Health"])
app.include_router(auth.router,        prefix="/api/auth",        tags=["Auth"])
app.include_router(users.router,       prefix="/api/users",       tags=["Users"])
app.include_router(portfolios.router,  prefix="/api/portfolios",  tags=["Portfolios"])
app.include_router(rebalancing.router, prefix="/api/rebalancing", tags=["Rebalancing"])
app.include_router(export_router,      prefix="/api/rebalancing", tags=["Export"])
app.include_router(audit.router,       prefix="/api/audit",       tags=["Audit"])
app.include_router(admin.router,       prefix="/api/admin",       tags=["Admin"])
