from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

_cors_origins = settings.cors_origins
# Always include the production frontend even if env var is misconfigured
_REQUIRED_ORIGINS = ["https://allocensus.vercel.app"]
for _o in _REQUIRED_ORIGINS:
    if _o not in _cors_origins:
        _cors_origins.append(_o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    origin = request.headers.get("origin", "")
    headers = {}
    if origin in _cors_origins:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    log.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=headers,
    )

if settings.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    sentry_sdk.init(dsn=settings.SENTRY_DSN, integrations=[FastApiIntegration()])

from app.routers import auth, users, portfolios, rebalancing, audit, admin, health
from app.routers.export import router as export_router

app.include_router(health.router,      prefix="/api",             tags=["Health"])
app.include_router(auth.router,        prefix="/api/auth",        tags=["Auth"])
app.include_router(users.router,       prefix="/api/users",       tags=["Users"])
app.include_router(portfolios.router,  prefix="/api/portfolios",  tags=["Portfolios"])
app.include_router(rebalancing.router, prefix="/api/rebalancing", tags=["Rebalancing"])
app.include_router(export_router,      prefix="/api/rebalancing", tags=["Export"])
app.include_router(audit.router,       prefix="/api/audit",       tags=["Audit"])
app.include_router(admin.router,       prefix="/api/admin",       tags=["Admin"])
