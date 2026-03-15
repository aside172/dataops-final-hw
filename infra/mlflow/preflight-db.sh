#!/usr/bin/env bash
set -Eeuo pipefail

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: ${name}" >&2
    exit 2
  fi
}

sql() {
  PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -v ON_ERROR_STOP=1 \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    -tAc "$1"
}

require_env POSTGRES_HOST
require_env POSTGRES_PORT
require_env POSTGRES_DB
require_env POSTGRES_USER
require_env POSTGRES_PASSWORD

table_count="$(sql "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")"
alembic_exists="$(sql "SELECT to_regclass('public.alembic_version') IS NOT NULL;")"
metrics_exists="$(sql "SELECT to_regclass('public.metrics') IS NOT NULL;")"
alembic_revision=""

if [[ "${alembic_exists}" == "t" ]]; then
  alembic_revision="$(sql "SELECT version_num FROM public.alembic_version LIMIT 1;")"
fi

echo "MLflow DB preflight:"
echo "  database=${POSTGRES_DB}"
echo "  schema=public"
echo "  table_count=${table_count}"
echo "  alembic_version_exists=${alembic_exists}"
if [[ -n "${alembic_revision}" ]]; then
  echo "  alembic_revision=${alembic_revision}"
fi
echo "  metrics_table_exists=${metrics_exists}"

if [[ "${table_count}" == "0" && "${alembic_exists}" == "f" && "${metrics_exists}" == "f" ]]; then
  echo "Preflight result: fresh empty database. Baseline MLflow schema initialization is required before migrations."
  exit 10
fi

if [[ "${metrics_exists}" == "t" && "${alembic_exists}" == "f" ]]; then
  echo "Preflight result: baseline MLflow tables exist without alembic_version. This is acceptable before running mlflow db upgrade."
  exit 0
fi

if [[ "${metrics_exists}" == "t" && "${alembic_exists}" == "t" ]]; then
  echo "Preflight result: existing MLflow schema detected. Safe to run migrations."
  exit 0
fi

echo "Preflight result: inconsistent MLflow database state detected."
echo "The database is not empty, but the required MLflow baseline tables are incomplete."
echo "Recommended action for this homework project: reset the MLflow PostgreSQL volume and start again."
echo "Manual reset command:"
echo "  docker compose down -v --remove-orphans"
echo "  rm -rf ../../artifacts/mlflow"
echo "  docker compose up --build"
exit 20
