"""
ALLOCENSUS — Phase 1 Scaffold Script
Creates: directory tree, Docker configs, CI/CD, environment files, requirements
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def mkdir(path):
    full = os.path.join(ROOT, path)
    os.makedirs(full, exist_ok=True)
    print(f"  DIR  {path}")

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  FILE {path}")

# ─── DIRECTORY TREE ──────────────────────────────────────────────────────────
print("\n[1/7] Creating directory tree...")
dirs = [
    "backend/app/models",
    "backend/app/schemas",
    "backend/app/routers",
    "backend/app/services",
    "backend/app/middleware",
    "backend/app/utils",
    "backend/app/workers",
    "backend/alembic/versions",
    "backend/tests/unit",
    "backend/tests/integration",
    "contracts",
    "frontend/src/app/(auth)/login",
    "frontend/src/app/(auth)/register",
    "frontend/src/app/(dashboard)/dashboard",
    "frontend/src/app/(dashboard)/portfolios/[id]",
    "frontend/src/app/(dashboard)/rebalancing/[id]",
    "frontend/src/app/(dashboard)/audit",
    "frontend/src/app/(dashboard)/settings",
    "frontend/src/app/admin",
    "frontend/src/components/ui",
    "frontend/src/components/portfolio",
    "frontend/src/components/rebalancing",
    "frontend/src/components/rationale",
    "frontend/src/components/charts",
    "frontend/src/components/layout",
    "frontend/src/lib",
    "frontend/src/hooks",
    "frontend/src/stores",
    "frontend/src/types",
    "frontend/public/images",
    "frontend/public/fonts",
    "docs",
    "tests/e2e",
    ".github/workflows",
]
for d in dirs:
    mkdir(d)

# ─── ROOT FILES ──────────────────────────────────────────────────────────────
print("\n[2/7] Writing root files...")

write(".gitignore", """\
# Python
__pycache__/
*.py[cod]
*.pyo
.venv/
venv/
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Node
node_modules/
.next/
out/
.turbo/

# Env
.env
.env.local
.env.*.local
!.env.example

# Docker
*.log

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp

# Keys / secrets
*.pem
*.key
keystore/
""")

write("README.md", """\
# ALLOCENSUS
**AI-Validated Portfolio Rebalancing Intelligence**

Powered by Genlayer Intelligent Contracts on StudioNet.

## Quick Start

```bash
# 1. Start backend + DB
cd backend && docker-compose up -d

# 2. Run migrations
docker-compose exec api alembic upgrade head

# 3. Start frontend
cd frontend && npm install && npm run dev
```

## Architecture
- **Frontend**: Next.js 14 — Vercel
- **Backend**: FastAPI (Python 3.12) — Railway
- **Database**: PostgreSQL 16 + Redis — Railway
- **Contract**: Genlayer Intelligent Contract — StudioNet

## Environment
Copy `.env.example` to `.env` in both `backend/` and `frontend/`.
""")

# ─── DOCKER ──────────────────────────────────────────────────────────────────
print("\n[3/7] Writing Docker configs...")

write("backend/docker-compose.yml", """\
version: "3.9"

services:
  db:
    image: postgres:16-alpine
    container_name: allocensus_db
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-allocensus}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-allocensus_dev}
      POSTGRES_DB: ${POSTGRES_DB:-allocensus}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-allocensus}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: allocensus_redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: allocensus_api
    env_file: .env
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-allocensus}:${POSTGRES_PASSWORD:-allocensus_dev}@db:5432/${POSTGRES_DB:-allocensus}
      REDIS_URL: redis://redis:6379/0
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./app:/app/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: allocensus_worker
    env_file: .env
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-allocensus}:${POSTGRES_PASSWORD:-allocensus_dev}@db:5432/${POSTGRES_DB:-allocensus}
      REDIS_URL: redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=4

volumes:
  pgdata:
  redisdata:
""")

write("backend/Dockerfile", """\
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \\
    build-essential \\
    libpq-dev \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
""")

write("backend/Dockerfile.prod", """\
FROM python:3.12-slim AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
""")

# ─── REQUIREMENTS ────────────────────────────────────────────────────────────
print("\n[4/7] Writing requirements.txt...")

write("backend/requirements.txt", """\
# Web framework
fastapi==0.115.5
uvicorn[standard]==0.32.1
python-multipart==0.0.12

# Database
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.0
psycopg2-binary==2.9.10

# Redis / Cache
redis[asyncio]==5.2.1
celery[redis]==5.4.0

# Auth & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
cryptography==43.0.3
mnemonic==0.21

# Wallet / Web3
eth-account==0.13.3
web3==7.5.0

# HTTP client (for Genlayer + price feeds)
httpx==0.28.0
aiohttp==3.11.8

# Validation
pydantic==2.10.2
pydantic-settings==2.6.1
email-validator==2.2.0

# Email
resend==2.4.0

# PDF generation
reportlab==4.2.5
pypdf==5.1.0

# Task queue
celery==5.4.0
flower==2.0.1

# Logging
structlog==24.4.0

# Testing
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==6.0.0
httpx==0.28.0
factory-boy==3.3.1

# Dev tools
ruff==0.8.1
mypy==1.13.0
pre-commit==4.0.1

# Monitoring
sentry-sdk[fastapi]==2.19.0
""")

# ─── BACKEND ENV ─────────────────────────────────────────────────────────────
print("\n[5/7] Writing environment files...")

write("backend/.env.example", """\
# ── Application ──────────────────────────────────────────────
APP_NAME=Allocensus
APP_ENV=development
DEBUG=true
SECRET_KEY=change-me-to-a-long-random-secret-key-32-chars-min
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# ── Database ─────────────────────────────────────────────────
POSTGRES_USER=allocensus
POSTGRES_PASSWORD=allocensus_dev
POSTGRES_DB=allocensus
DATABASE_URL=postgresql+asyncpg://allocensus:allocensus_dev@localhost:5432/allocensus
DATABASE_URL_SYNC=postgresql://allocensus:allocensus_dev@localhost:5432/allocensus

# ── Redis ────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ── JWT ──────────────────────────────────────────────────────
JWT_SECRET_KEY=change-me-to-another-long-random-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ── Wallet Encryption ────────────────────────────────────────
WALLET_ENCRYPTION_KEY=change-me-32-bytes-hex-encoded-key
WALLET_PBKDF2_ITERATIONS=310000

# ── Genlayer ─────────────────────────────────────────────────
GENLAYER_RPC_URL=https://studio.genlayer.com/api
GENLAYER_CONTRACT_ADDRESS=
GENLAYER_DEPLOYER_PRIVATE_KEY=

# ── Price Feeds ──────────────────────────────────────────────
COINGECKO_API_KEY=
YAHOO_FINANCE_ENABLED=true

# ── Email ────────────────────────────────────────────────────
RESEND_API_KEY=
EMAIL_FROM=noreply@allocensus.com
EMAIL_FROM_NAME=Allocensus

# ── Storage (Cloudflare R2) ──────────────────────────────────
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=allocensus-reports
R2_PUBLIC_URL=

# ── Monitoring ───────────────────────────────────────────────
SENTRY_DSN=

# ── Rate Limiting ────────────────────────────────────────────
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=20
""")

write("frontend/.env.example", """\
# ── API ──────────────────────────────────────────────────────
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# ── App ──────────────────────────────────────────────────────
NEXT_PUBLIC_APP_NAME=Allocensus
NEXT_PUBLIC_APP_URL=http://localhost:3000

# ── Genlayer ─────────────────────────────────────────────────
NEXT_PUBLIC_GENLAYER_RPC_URL=https://studio.genlayer.com/api
NEXT_PUBLIC_CONTRACT_ADDRESS=

# ── Monitoring ───────────────────────────────────────────────
NEXT_PUBLIC_SENTRY_DSN=
NEXT_PUBLIC_POSTHOG_KEY=
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com
""")

# ─── GITHUB ACTIONS ──────────────────────────────────────────────────────────
print("\n[6/7] Writing GitHub Actions CI/CD...")

write(".github/workflows/ci.yml", """\
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-test:
    name: Backend Tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: allocensus_test
          POSTGRES_PASSWORD: allocensus_test
          POSTGRES_DB: allocensus_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: backend/requirements.txt
      - name: Install dependencies
        working-directory: backend
        run: pip install -r requirements.txt
      - name: Lint
        working-directory: backend
        run: ruff check app tests
      - name: Type check
        working-directory: backend
        run: mypy app
      - name: Run tests
        working-directory: backend
        env:
          DATABASE_URL: postgresql+asyncpg://allocensus_test:allocensus_test@localhost:5432/allocensus_test
          DATABASE_URL_SYNC: postgresql://allocensus_test:allocensus_test@localhost:5432/allocensus_test
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key-for-ci-minimum-32-chars
          JWT_SECRET_KEY: test-jwt-secret-for-ci-minimum-32-chars
          WALLET_ENCRYPTION_KEY: 0000000000000000000000000000000000000000000000000000000000000000
        run: pytest tests/ -v --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: backend/coverage.xml

  frontend-test:
    name: Frontend Build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - name: Install
        working-directory: frontend
        run: npm ci
      - name: Type check
        working-directory: frontend
        run: npm run type-check
      - name: Lint
        working-directory: frontend
        run: npm run lint
      - name: Build
        working-directory: frontend
        env:
          NEXT_PUBLIC_API_URL: http://localhost:8000
          NEXT_PUBLIC_APP_NAME: Allocensus
        run: npm run build
""")

write(".github/workflows/deploy.yml", """\
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    name: Deploy Backend to Railway
    runs-on: ubuntu-latest
    needs: []
    steps:
      - uses: actions/checkout@v4
      - name: Install Railway CLI
        run: npm install -g @railway/cli
      - name: Deploy
        working-directory: backend
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: railway up --service allocensus-api

  deploy-migrations:
    name: Run DB Migrations
    runs-on: ubuntu-latest
    needs: [deploy-backend]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install
        working-directory: backend
        run: pip install -r requirements.txt
      - name: Migrate
        working-directory: backend
        env:
          DATABASE_URL_SYNC: ${{ secrets.RAILWAY_DATABASE_URL_SYNC }}
        run: alembic upgrade head
""")

# ─── ALEMBIC ─────────────────────────────────────────────────────────────────
print("\n[7/7] Writing Alembic config...")

write("backend/alembic.ini", """\
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://allocensus:allocensus_dev@localhost:5432/allocensus

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
""")

write("backend/alembic/env.py", """\
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import Base
from app.models import *  # noqa: F401,F403 — import all models for autogenerate

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

DATABASE_URL = os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "").replace(
    "postgresql+asyncpg://", "postgresql://"
)
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    config_section = config.get_section(config.config_ini_section, {})
    config_section["sqlalchemy.url"] = DATABASE_URL
    connectable = async_engine_from_config(
        config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
""")

write("backend/alembic/versions/.gitkeep", "")

# ─── PYPROJECT / RUFF / MYPY ─────────────────────────────────────────────────
write("backend/pyproject.toml", """\
[tool.ruff]
target-version = "py312"
line-length = 100
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
ignore = ["E501", "B008", "N818"]

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
env = [
    "APP_ENV=test",
]
""")

print("\n✅ Phase 1 scaffold complete.")
print(f"   Root: {ROOT}")
