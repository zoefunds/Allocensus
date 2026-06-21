#!/bin/bash
set -e

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║           ALLOCENSUS — Dev Environment           ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Check Docker
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker is not running. Start Docker Desktop first."
  exit 1
fi

# Copy .env if not present
if [ ! -f backend/.env ]; then
  echo "📋 Copying backend .env.example → .env"
  cp backend/.env.example backend/.env
  echo "⚠️  Edit backend/.env with your secrets before proceeding."
fi

if [ ! -f frontend/.env.local ]; then
  echo "📋 Copying frontend .env.example → .env.local"
  cp frontend/.env.example frontend/.env.local
fi

echo ""
echo "🐳 Starting PostgreSQL + Redis + API..."
cd backend && docker-compose up -d db redis

echo ""
echo "⏳ Waiting for database to be ready..."
sleep 5

echo ""
echo "🗄️  Running migrations..."
docker-compose run --rm api alembic upgrade head || echo "⚠️  Migration skipped (API container may need image build first)"

echo ""
echo "🚀 Starting API server..."
docker-compose up -d api worker

echo ""
echo "📦 Installing frontend dependencies..."
cd ../frontend
if [ ! -d node_modules ]; then
  npm install
fi

echo ""
echo "✅ Backend running at http://localhost:8000"
echo "   API docs:    http://localhost:8000/api/docs"
echo ""
echo "▶  Starting frontend..."
npm run dev
