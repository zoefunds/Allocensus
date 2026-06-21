# ALLOCENSUS
**AI-Validated Portfolio Rebalancing Intelligence**

Institutional-grade portfolio rebalancing decisions powered by Genlayer AI validator consensus — transparent, auditable, and on-chain.

---

## What It Does

Allocensus replaces the black-box AI investment tool with something defensible. When a portfolio manager proposes a rebalancing, it is submitted to **Genlayer's validator network** — multiple independent AI nodes evaluate it against constraint rules, market data, and investor profile. The consensus result (approved/rejected + full rationale) is written permanently on-chain.

Every decision is traceable, reproducible, and audit-ready.

---

## Live Links

| Service | URL |
|---------|-----|
| Frontend | https://allocensus.vercel.app |
| Backend API | https://allocensus-api.fly.dev |
| API Docs | https://allocensus-api.fly.dev/api/docs |
| Genlayer Explorer | https://explorer-studio.genlayer.com |

---

## Architecture

```
┌─────────────────────┐        ┌──────────────────────┐
│   Next.js Frontend  │◄──────►│  FastAPI Backend      │
│   (Vercel)          │  REST  │  (Fly.io, lhr region) │
└─────────────────────┘        └──────────┬───────────┘
                                           │
                         ┌─────────────────┼─────────────────┐
                         │                 │                   │
                  ┌──────▼──────┐  ┌──────▼──────┐  ┌───────▼──────┐
                  │ PostgreSQL  │  │    Redis     │  │  Genlayer    │
                  │ (Fly.io)    │  │  (Fly.io)   │  │  StudioNet   │
                  └─────────────┘  └─────────────┘  └──────────────┘
```

### Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16 (App Router), TypeScript, Tailwind CSS, zustand, React Query |
| Backend | FastAPI, Python 3.12, SQLAlchemy async, Alembic |
| Database | PostgreSQL 16 (Fly.io managed) |
| Cache | Redis 7 (Fly.io managed) |
| Hosting | Frontend → Vercel · Backend → Fly.io (London, always-on) |
| Blockchain | Genlayer StudioNet (Chain ID 61999) |
| Smart Contract | Python Intelligent Contract — `PortfolioRebalancingRationale` |

---

## Genlayer Integration

### Contract

| Field | Value |
|-------|-------|
| Network | Genlayer StudioNet |
| Chain ID | 61999 |
| RPC | `https://studio.genlayer.com/api` |
| Contract Address | `0x2EDfB701Afe68259c7468b24ba0AAa7Ac24368cC` |
| Consensus Main Contract | `0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575` |
| Gas | Free (StudioNet has no gas fees) |

### Transaction Flow

1. User creates a rebalancing proposal (frontend)
2. Backend builds unsigned calldata via `evaluate_rebalancing(proposal_id, current_portfolio, proposed_portfolio, market_context)`
3. Frontend signs with the user's encrypted keystore (password-derived — private key never leaves the browser)
4. Transaction is sent to the **Consensus Main Contract** via `addTransaction(sender, contractAddress, numValidators=5, maxRotations=3, encodedCalldata)`
5. 5 Genlayer validators independently run the intelligent contract (Python + web AI calls)
6. Consensus result written on-chain — frontend polls `eth_getTransactionByHash` until `status: FINALIZED`
7. Backend reads result via `gen_call` → `get_proposal(proposal_id)` view method

### Security Constraint

**The backend never touches private keys.** All transactions are signed client-side by the user's wallet using their password-decrypted keystore (Web3 V3 / ethers.js `Wallet.fromEncryptedJson`). The backend only builds unsigned calldata.

---

## Repository Structure

```
ALLOCENSUS/
├── frontend/                    # Next.js app
│   ├── src/
│   │   ├── app/                 # App Router pages
│   │   │   ├── (auth)/          # login, register, forgot-password
│   │   │   ├── (dashboard)/     # dashboard, portfolios, rebalancing, audit, settings
│   │   │   └── page.tsx         # Landing page
│   │   ├── components/
│   │   │   ├── layout/          # DashboardNav, Providers
│   │   │   ├── rebalancing/     # SubmitToGenlayerModal
│   │   │   └── ui/              # Button, Card, Input, Badge, etc.
│   │   ├── hooks/
│   │   │   └── useGenlayerTx.ts # Genlayer transaction signing + submission
│   │   ├── lib/
│   │   │   └── api.ts           # Axios API client
│   │   └── stores/
│   │       └── auth.ts          # zustand auth + wallet store (persisted)
│   └── public/
│       └── logo.png             # Allocensus logo
│
├── backend/                     # FastAPI app
│   ├── app/
│   │   ├── routers/             # auth, users, portfolios, rebalancing, audit, admin, export
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── genlayer_service.py   # RPC calls, calldata encoding, finalization polling
│   │   │   ├── rebalancing_service.py
│   │   │   └── wallet_service.py     # Web3 V3 keystore generation
│   │   └── utils/
│   │       ├── constraints.py   # 8 portfolio constraint rules
│   │       └── security.py      # bcrypt, JWT, AES-256-GCM wallet encryption
│   ├── alembic/                 # DB migrations
│   ├── fly.toml                 # Fly.io config (auto_stop_machines = false)
│   └── Dockerfile
│
├── contracts/
│   └── portfolio_rebalancing_rationale.py   # Genlayer intelligent contract
│
└── .github/
    └── workflows/
        ├── deploy.yml           # Fly.io + Vercel deploy on push to main
        └── ci.yml               # Backend lint + frontend build check
```

---

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker (for local PostgreSQL + Redis)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env — set DATABASE_URL, REDIS_URL, JWT_SECRET_KEY, etc.

# Start local PostgreSQL + Redis
docker compose up -d db redis

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8080
```

Backend available at `http://localhost:8080` · Docs at `http://localhost:8080/api/docs`

### Frontend

```bash
cd frontend

# Install dependencies
npm install --legacy-peer-deps

# Copy environment file
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8080

# Start dev server
npm run dev
```

Frontend available at `http://localhost:3000`

---

## Environment Variables

### Backend (`.env`)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Async PostgreSQL URL (`postgresql+asyncpg://...`) |
| `DATABASE_URL_SYNC` | Sync PostgreSQL URL for Alembic (`postgresql://...`) |
| `REDIS_URL` | Redis connection URL |
| `JWT_SECRET_KEY` | Secret for signing JWTs (min 32 chars) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Default: 60 |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Default: 7 |
| `GENLAYER_RPC_URL` | `https://studio.genlayer.com/api` |
| `GENLAYER_CONTRACT_ADDRESS` | `0x2EDfB701Afe68259c7468b24ba0AAa7Ac24368cC` |
| `WALLET_ENCRYPTION_KEY` | 64-char hex key for server-side wallet encryption |
| `WALLET_PBKDF2_ITERATIONS` | Default: 100000 |
| `SENDGRID_API_KEY` | For email verification (optional) |
| `COINGECKO_API_KEY` | For live market data enrichment (optional) |

### Frontend (`.env.local`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend URL (e.g. `https://allocensus-api.fly.dev`) |
| `NEXT_PUBLIC_APP_URL` | Frontend URL |
| `NEXT_PUBLIC_APP_NAME` | `Allocensus` |
| `NEXT_PUBLIC_GENLAYER_RPC_URL` | `https://studio.genlayer.com/api` |
| `NEXT_PUBLIC_CONTRACT_ADDRESS` | `0x2EDfB701Afe68259c7468b24ba0AAa7Ac24368cC` |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/register` | Create account + provision wallet |
| `POST` | `/api/auth/login` | Login, returns JWT |
| `POST` | `/api/auth/refresh` | Refresh access token |
| `GET` | `/api/users/me` | Current user profile |
| `GET` | `/api/portfolios` | List portfolios |
| `POST` | `/api/portfolios` | Create portfolio |
| `GET` | `/api/portfolios/{id}` | Get portfolio with assets |
| `PUT` | `/api/portfolios/{id}` | Update portfolio |
| `DELETE` | `/api/portfolios/{id}` | Delete portfolio |
| `GET` | `/api/rebalancing` | List proposals |
| `POST` | `/api/rebalancing` | Create proposal (runs constraint checks) |
| `GET` | `/api/rebalancing/{id}` | Get proposal |
| `DELETE` | `/api/rebalancing/{id}` | Delete proposal (DRAFT/PENDING/FAILED only) |
| `GET` | `/api/rebalancing/{id}/call-data` | Build unsigned Genlayer calldata |
| `POST` | `/api/rebalancing/{id}/confirm-tx` | Record submitted tx hash |
| `GET` | `/api/rebalancing/{id}/poll` | Poll consensus finalization |
| `GET` | `/api/rebalancing/{id}/export/pdf` | Export proposal as PDF |
| `GET` | `/api/rebalancing/{id}/export/csv` | Export proposal as CSV |
| `GET` | `/api/audit/events` | Audit event log |
| `GET` | `/api/audit/compliance` | Compliance log |
| `GET` | `/api/admin/users` | List all users (admin only) |
| `GET` | `/api/health` | Health check (DB + Redis) |

---

## Deployment

### Backend (Fly.io)

```bash
cd backend
fly deploy --remote-only
```

Machine: 1 shared CPU, 512 MB RAM, London region (`lhr`), always-on (`auto_stop_machines = false`).

### Frontend (Vercel)

```bash
cd frontend
npx vercel deploy --prod --yes
```

### Database Migrations (production)

```bash
flyctl ssh console --app allocensus-api --command "cd /app && alembic upgrade head"
```

---

## Key Design Decisions

**Wallet security** — Each user gets a Web3 V3 keystore generated at registration. The private key is encrypted with AES-256-GCM using a key derived from the user's password via PBKDF2-SHA256. The server never stores or has access to the plaintext private key — only the user's password can decrypt it client-side.

**Genlayer calldata encoding** — Transactions use a custom binary format (not JSON). Map keys are length-prefixed with no type tag; values carry a type varint `(len << 3) | type`. Maps are sorted alphabetically. The encoded calldata is RLP-serialized as `[calldataBytes, false]` before being passed to `addTransaction` on the Consensus Main Contract.

**Constraint checks** — 8 rules are enforced server-side before any proposal reaches Genlayer: concentration limits, asset class diversification, liquidity requirements, drift thresholds, and more. Violations block submission and are returned to the user with specific messages.

**No gas fees** — Genlayer StudioNet is a gasless network. All transactions are free.

---

## License

Private — all rights reserved. © 2026 Allocensus / ZoeFunds.
