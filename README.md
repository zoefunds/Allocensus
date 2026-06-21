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
