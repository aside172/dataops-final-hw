#!/usr/bin/env bash
set -Eeuo pipefail

mode="${1:-server}"

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: ${name}" >&2
    exit 1
  fi
}

wait_for_postgres() {
  echo "Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}..."
  for _ in $(seq 1 60); do
    if pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" >/dev/null 2>&1; then
      echo "PostgreSQL is ready."
      return 0
    fi
    sleep 2
  done
  echo "PostgreSQL did not become ready in time." >&2
  exit 1
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

reset_public_schema() {
  echo "Resetting public schema in ${POSTGRES_DB}..."
  PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -v ON_ERROR_STOP=1 \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" <<SQL
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO ${POSTGRES_USER};
GRANT ALL ON SCHEMA public TO public;
SQL
}

bootstrap_baseline_schema() {
  echo "Initializing baseline MLflow schema on empty database..."
  python - <<'PY'
import os
from mlflow.store.db.utils import _initialize_tables, create_sqlalchemy_engine

engine = create_sqlalchemy_engine(os.environ["BACKEND_STORE_URI"])
_initialize_tables(engine)
PY
}

run_preflight() {
  set +e
  /usr/local/bin/mlflow-preflight-db.sh
  local rc=$?
  set -e

  case "${rc}" in
    0)
      return 0
      ;;
    10)
      bootstrap_baseline_schema
      return 0
      ;;
    20)
      echo "MLflow preflight detected an inconsistent PostgreSQL schema." >&2
      if [[ "${MLFLOW_DB_RESET_ON_INCONSISTENT_STATE:-false}" == "true" ]]; then
        echo "MLFLOW_DB_RESET_ON_INCONSISTENT_STATE=true, resetting public schema and reinitializing baseline tables..."
        reset_public_schema
        bootstrap_baseline_schema
        return 0
      fi
      echo "Automatic reset is disabled." >&2
      echo "Run a full Docker volume reset for the MLflow stack and start again." >&2
      exit 1
      ;;
    *)
      echo "MLflow preflight failed unexpectedly with exit code ${rc}." >&2
      exit "${rc}"
      ;;
  esac
}

run_migrations() {
  echo "Running mlflow db upgrade..."
  mlflow db upgrade "${BACKEND_STORE_URI}"
}

start_server() {
  echo "Starting MLflow server..."
  exec mlflow server \
    --backend-store-uri "${BACKEND_STORE_URI}" \
    --artifacts-destination "${ARTIFACT_ROOT}" \
    --host 0.0.0.0 \
    --port "${MLFLOW_PORT:-5001}"
}

require_env BACKEND_STORE_URI
require_env ARTIFACT_ROOT
require_env POSTGRES_HOST
require_env POSTGRES_PORT
require_env POSTGRES_DB
require_env POSTGRES_USER
require_env POSTGRES_PASSWORD

wait_for_postgres
run_preflight

case "${mode}" in
  migrate)
    run_migrations
    ;;
  server)
    start_server
    ;;
  *)
    exec "$@"
    ;;
esac
