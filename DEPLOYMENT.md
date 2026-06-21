# Allocensus — Deployment Guide

## URLs
- Frontend : https://allocensus.vercel.app
- Backend  : https://allocensus-api.up.railway.app
- GitHub   : https://github.com/zoefunds/Allocensus
- Contract : 0xe45A5379bDD30BF75D08752cb32c4178f59445EA (Genlayer StudioNet)

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

## Step 2 — Railway (Backend)

1. railway.app → New Project → Deploy from GitHub → zoefunds/Allocensus
2. Root directory: `backend`
3. Add environment variables (Railway dashboard → Variables):

```
APP_ENV=production
SECRET_KEY=<from backend/.env>
JWT_SECRET_KEY=<from backend/.env>
WALLET_ENCRYPTION_KEY=<from backend/.env>
ALLOWED_ORIGINS=https://allocensus.vercel.app
DATABASE_URL=<Railway PostgreSQL internal URL>
DATABASE_URL_SYNC=<Railway PostgreSQL sync URL>
REDIS_URL=<your Upstash Redis URL>
GENLAYER_RPC_URL=https://studio.genlayer.com/api
GENLAYER_CONTRACT_ADDRESS=0xe45A5379bDD30BF75D08752cb32c4178f59445EA
BREVO_API_KEY=<your Brevo API key>
EMAIL_FROM=preciousmofeoluwa@gmail.com
EMAIL_FROM_NAME=Allocensus
```

4. After first deploy → Railway shell → `alembic upgrade head`
5. Note the Railway service URL

---

## Step 3 — Vercel (Frontend)

1. vercel.com → New Project → Import → zoefunds/Allocensus
2. Root Directory: `frontend`
3. Framework Preset: Next.js
4. Environment variables:

```
NEXT_PUBLIC_API_URL=https://allocensus-api.up.railway.app
NEXT_PUBLIC_GENLAYER_RPC_URL=https://studio.genlayer.com/api
NEXT_PUBLIC_CONTRACT_ADDRESS=0xe45A5379bDD30BF75D08752cb32c4178f59445EA
NEXT_PUBLIC_APP_URL=https://allocensus.vercel.app
```

5. Deploy → set custom domain to allocensus.vercel.app in Vercel → Domains

---

## Step 4 — GitHub Actions Secrets

Settings → Secrets → Actions → New repository secret:

| Secret | Where to get it |
|--------|----------------|
| `RAILWAY_TOKEN` | Railway → Account Settings → Tokens |
| `RAILWAY_DATABASE_URL_SYNC` | Railway → PostgreSQL service → Variables |
| `VERCEL_TOKEN` | Vercel → Settings → Tokens |
| `VERCEL_ORG_ID` | Vercel → Settings → General |
| `VERCEL_PROJECT_ID` | Vercel → Project → Settings |

After secrets are set, every push to `main` auto-deploys both Railway and Vercel.

---

## Step 5 — Verify

```bash
# Backend health
curl https://allocensus-api.up.railway.app/api/health

# API docs
open https://allocensus-api.up.railway.app/api/docs

# Frontend
open https://allocensus.vercel.app
```
