#!/bin/bash
set -e
cd backend
source .venv/bin/activate 2>/dev/null || true
pytest tests/ -v --cov=app --cov-report=term-missing
