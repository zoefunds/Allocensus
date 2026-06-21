#!/bin/bash
echo "🛑 Stopping Allocensus dev environment..."
cd backend && docker-compose down
echo "✅ Done."
