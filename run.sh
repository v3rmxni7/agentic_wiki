#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt
if [ ! -f .env ]; then
  cp .env.example .env
  echo "created .env - add your GROQ_API_KEY or set MOCK_MODE=1"
fi
export PYTHONPATH="$(pwd)"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
