# Allocensus — Deployment Guide

## URLs
- Frontend : https://allocensus.vercel.app
- Backend  : https://allocensus-backend-zoe.fly.dev
- GitHub   : https://github.com/zoefunds/Allocensus
- Contract : 0x6501ecf77Cd3A559dDF5Eed16bc803b4aCBC56Ca (Genlayer StudioNet)

---

## Step 1 — Push to GitHub

```bash
cd /Users/macbook/ALLOCENSUS
git init
git remote add origin https://github.com/zoefunds/Allocensus.git
git add .
git commit -m "feat: initial production build"
git branch -M main
git push -u origin main
```

---

## Step 2 — Fly.io Backend

1. fly.io → New App → Deploy from GitHub → zoefunds/Allocensus
2. Root directory: `backend`
3. Add environment variables (Fly dashboard → Secrets):

```
APP_ENV=production
SECRET_KEY=<from backend/.env>
JWT_SECRET_KEY=<from backend/.env>
WALLET_ENCRYPTION_KEY=<from backend/.env>
ALLOWED_ORIGINS=https://allocensus.vercel.app
DATABASE_URL=<Fly PostgreSQL internal URL>
DATABASE_URL_SYNC=<Fly PostgreSQL sync URL>
REDIS_URL=<your Redis URL>
GENLAYER_RPC_URL=https://studio.genlayer.com/api
GENLAYER_CONTRACT_ADDRESS=0x6501ecf77Cd3A559dDF5Eed16bc803b4aCBC56Ca
BREVO_API_KEY=<your Brevo API key>
EMAIL_FROM=preciousmofeoluwa@gmail.com
EMAIL_FROM_NAME=Allocensus
```

4. After first deploy → Fly SSH console → `sh -lc "cd /app && alembic upgrade head"`
5. Note the Fly service URL

---

## Step 3 — Vercel (Frontend)

1. vercel.com → New Project → Import → zoefunds/Allocensus
2. Root Directory: `frontend`
3. Framework Preset: Next.js
4. Environment variables:

```
NEXT_PUBLIC_API_URL=https://allocensus-backend-zoe.fly.dev
NEXT_PUBLIC_GENLAYER_RPC_URL=https://studio.genlayer.com/api
NEXT_PUBLIC_CONTRACT_ADDRESS=0x6501ecf77Cd3A559dDF5Eed16bc803b4aCBC56Ca
NEXT_PUBLIC_APP_URL=https://allocensus.vercel.app
```

5. Deploy → set custom domain to allocensus.vercel.app in Vercel → Domains

---

## Step 4 — GitHub Actions Secrets

Settings → Secrets → Actions → New repository secret:

| Secret | Where to get it |
|--------|----------------|
| `FLY_API_TOKEN` | Fly.io → Account settings → Tokens |
| `FLY_DATABASE_URL_SYNC` | Fly PostgreSQL service → connection string |
| `VERCEL_TOKEN` | Vercel → Settings → Tokens |
| `VERCEL_ORG_ID` | Vercel → Settings → General |
| `VERCEL_PROJECT_ID` | Vercel → Project → Settings |

After secrets are set, every push to `main` auto-deploys both Fly and Vercel.

---

## Step 5 — Verify

```bash
# Backend health
curl https://allocensus-backend-zoe.fly.dev/api/health

# API docs
open https://allocensus-backend-zoe.fly.dev/api/docs

# Frontend
open https://allocensus.vercel.app
```
