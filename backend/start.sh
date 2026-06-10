#!/usr/bin/env bash
# Render startup script — verifies the app imports before binding to $PORT.
set -euo pipefail

cd "$(dirname "$0")"

echo "==> Python: $(python --version)"
echo "==> Working directory: $(pwd)"
echo "==> APP_ENV=${APP_ENV:-unset}"
echo "==> DATABASE_URL is ${DATABASE_URL:+set}${DATABASE_URL:-unset}"

echo "==> Verifying application import..."
python -c "
from app.core.config import settings
print('  settings OK, env=', settings.APP_ENV, 'cors=', settings.cors_origins)
from app.main import app
print('  app OK, title=', app.title)
"

echo "==> Starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers 1 \
  --timeout-keep-alive 75 \
  --log-level info
