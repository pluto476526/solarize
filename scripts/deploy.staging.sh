#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# =============================================================================
# Solarize – Staging Deployment (Isolated from Production)
# =============================================================================

COMPOSE="docker-compose -f docker-compose.staging.yml -p solarize_staging"

APP_SERVICE="solarize-app-staging"
DB_SERVICE="solarize-db-staging"
REDIS_SERVICE="solarize-redis-staging"
CELERY_SERVICE="solarize-celery-staging"
CELERY_BEAT_SERVICE="solarize-celery-beat-staging"

DB_USER="pluto"
DB_NAME="solarize_staging"
SQL_SCRIPT="schema_setup.sql"

MAX_RETRIES=20
SLEEP_INTERVAL=3

log()    { echo -e "\n\033[1;36m>>> $*\033[0m"; }
error()  { echo -e "\033[1;31m!!! ERROR: $*\033[0m" >&2; }
status() { echo -e "    \033[1;33m→ $*\033[0m"; }

# --------------------------- 1. Rebuild images ------------------------------
log "Rebuilding staging Docker images"
$COMPOSE build || { error "Build failed"; exit 1; }

# ------------------------ 2. Start DB + Redis --------------------------------
log "Starting staging DB and Redis"
$COMPOSE up -d db redis

# ------------------------ 3. Wait for PostgreSQL -----------------------------
log "Waiting for staging PostgreSQL to become ready"

retry=0
while true; do
    retry=$((retry + 1))

    if docker ps --filter "name=^${DB_SERVICE}$" --filter "status=running" -q >/dev/null; then
        if docker exec "$DB_SERVICE" pg_isready -h localhost -U "$DB_USER" -d "$DB_NAME" -q; then
            log "Staging PostgreSQL is ready"
            break
        else
            status "Database responding but not ready"
        fi
    else
        status "DB container not yet running"
    fi

    if (( retry >= MAX_RETRIES )); then
        error "Timeout waiting for staging DB"
        docker logs "$DB_SERVICE" | tail -40
        exit 1
    fi

    status "Retry $retry/$MAX_RETRIES – sleeping $SLEEP_INTERVAL seconds"
    sleep "$SLEEP_INTERVAL"
done

# --------------------- 4. Ensure TimescaleDB exists -------------------------
log "Ensuring TimescaleDB is enabled in staging"
docker exec "$DB_SERVICE" psql -U "$DB_USER" -d "$DB_NAME" \
    -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# --------------------- 5. Apply custom SQL schema ---------------------------
if [[ -f "data_factory/database/$SQL_SCRIPT" ]]; then
    log "Applying staging SQL schema: $SQL_SCRIPT"
    docker cp "data_factory/database/$SQL_SCRIPT" "$DB_SERVICE":/tmp/schema_setup.sql
    docker exec "$DB_SERVICE" psql -U "$DB_USER" -d "$DB_NAME" \
        -f /tmp/schema_setup.sql
else
    status "No custom SQL script for staging"
fi

# --------------------- 6. Start app and workers -----------------------------
log "Starting staging app and Celery services"

$COMPOSE up -d --no-deps --build \
    app celery celery-beat nginx || {
    error "Failed to start staging services"
    exit 1
}

sleep 5

if ! docker ps --filter "name=^${APP_SERVICE}$" --filter "status=running" -q >/dev/null; then
    error "Staging app container failed to start"
    docker logs "$APP_SERVICE" | tail -40
    exit 1
fi

# --------------------------- 7. Run migrations ------------------------------
log "Running staging Django migrations"
docker exec "$APP_SERVICE" python manage.py migrate --noinput

log "Staging deployment successful"

echo
$COMPOSE ps
echo

