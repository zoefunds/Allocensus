#!/bin/bash
# For running backend locally without Docker (e.g. for development/testing)
set -e

cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
echo "✅ Backend venv created. Edit backend/.env then run:"
echo "   source backend/.venv/bin/activate"
echo "   uvicorn app.main:app --reload"
