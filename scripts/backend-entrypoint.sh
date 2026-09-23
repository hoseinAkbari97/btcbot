#!/bin/sh
set -eu

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  (
    cd "${BACKEND_DIR:-/app/backend}"
    alembic upgrade head
  )
fi
exec "$@"
