#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -x ./venv/bin/python ]]; then
  echo "Backend environment is missing. Run ./setup-backend.sh first." >&2
  exit 1
fi

exec ./venv/bin/python -m uvicorn main:app --reload
