#!/bin/bash
echo "⚠️  This will destroy all data. Ctrl+C to cancel."
sleep 3
cd backend
docker-compose down -v
docker-compose up -d db redis
sleep 5
docker-compose run --rm api alembic upgrade head
echo "✅ Database reset and migrated."
