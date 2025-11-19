root@wgvpn:/var/www/solarize# cat deploy.sh 
#!/bin/bash
# =============================================================================
# Solarize – Production-grade, zero-downtime deploy script with FULL DEBUGGING
# =============================================================================

set -euo pipefail
IFS=$'\n\t'

set -a
source .env
set +a

# ----------------------------- CONFIG ---------------------------------------
APP_SERVICE="solarize-app"
DB_SERVICE="solarize-db"
REDIS_SERVICE="solarize-redis"
CELERY_SERVICE="celery"
CELERY_BEAT_SERVICE="celery-beat"

DB_USER=$DB_USER
DB_NAME=$DB_NAME
SQL_SCRIPT="schema_setup.sql"

MAX_RETRIES=20
SLEEP_INTERVAL=3

log()    { echo -e "\n\033[1;36m>>> $*\033[0m"; }
error()  { echo -e "\033[1;31m!!! ERROR: $*\033[0m" >&2; }
status() { echo -e "    \033[1;33m→ $*\033[0m"; }

# --------------------------- 1. Rebuild images ------------------------------
log "Step 1/7 – Rebuilding Docker images (with latest base images)"
docker-compose build || { error "Image build failed"; exit 1; }

# ------------------------ 2. Start DB + Redis --------------------------------
log "Step 2/7 – Ensuring database and Redis are running"
docker-compose up -d db redis

# ------------------------ 3. Wait for PostgreSQL -----------------------------
log "Step 3/7 – Waiting for PostgreSQL/TimescaleDB to be fully ready (max $((MAX_RETRIES * SLEEP_INTERVAL))s)"

retry=0
while true; do
    retry=$((retry + 1))

    # 1. Check if container exists and is running
    if ! docker ps --filter "name=^${DB_SERVICE}$" --filter "status=running" -q >/dev/null 2>&1; then
        state=$(docker inspect --format='{{.State.Status}}' "$DB_SERVICE" 2>/dev/null || echo "MISSING")
        status "DB container state: $state (still starting or crashed)"
        if [[ "$state" == "exited" || "$state" == "dead" ]]; then
            error "Database container died! Showing logs..."
            docker logs "$DB_SERVICE" | tail -30
            exit 1
        fi
    else
        # 2. Container is running → test real DB connectivity
        if docker exec "$DB_SERVICE" pg_isready -h localhost -U "$DB_USER" -d "$DB_NAME" -q 2>/dev/null; then
            log "PostgreSQL is ready and accepting connections!"
            break
        else
            status "DB container is running but pg_isready reports not ready yet"
        fi
    fi

    # Timeout
    if (( retry >= MAX_RETRIES )); then
        error "TIMEOUT: Database did not become ready after $((MAX_RETRIES * SLEEP_INTERVAL)) seconds"
        echo
        log "Final container inspection:"
        docker inspect "$DB_SERVICE" | jq -r '.[] | .Name + " → " + .State.Status + " (exit " + (.State.ExitCode|tostring) + ")"' 2>/dev/null || echo "jq not available"
        echo
        log "Last 40 lines of DB logs:"
        docker logs --tail 40 "$DB_SERVICE"
        exit 1
    fi

    status "Attempt $retry/$MAX_RETRIES – sleeping ${SLEEP_INTERVAL}s..."
    sleep "$SLEEP_INTERVAL"
done

# --------------------- 4. Enable TimescaleDB extension ----------------------
log "Step 4/7 – Ensuring TimescaleDB extension exists"
if docker exec "$DB_SERVICE" psql -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS timescaledb;" -qtA; then
    echo "TimescaleDB extension ready"
else
    error "Failed to create TimescaleDB extension"
    exit 1
fi

# --------------------- 5. Apply custom SQL schema ---------------------------
if [[ -f "data_factory/database/$SQL_SCRIPT" ]]; then
    log "Step 5/7 – Applying custom schema: $SQL_SCRIPT"
    docker cp "data_factory/database/$SQL_SCRIPT" "$DB_SERVICE":/tmp/schema_setup.sql
    if docker exec "$DB_SERVICE" psql -U "$DB_USER" -d "$DB_NAME" -f /tmp/schema_setup.sql; then
        echo "Custom schema applied successfully"
    else
        error "Custom SQL script failed!"
        exit 1
    fi
else
    status "No custom SQL script found – skipping"
fi

# --------------------- 6. Start app + workers  ------------------------
log "Step 6/7 – Deploying application containers"
docker-compose up -d --no-deps --build \
    app celery celery-beat nginx || {
    error "Failed to start application containers"
    docker-compose ps
    exit 1
}

# Wait a moment for the app container to fully boot
sleep 5

# Verify app container is actually running
if ! docker ps --filter "name=^${APP_SERVICE}$" --filter "status=running" -q >/dev/null; then
    error "App container failed to start!"
    docker logs "$APP_SERVICE" | tail -30
    exit 1
fi

# --------------------------- 7. Run migrations -----------------------------
log "Step 7/7 – Running Django migrations"
if docker exec "$APP_SERVICE" python manage.py migrate --noinput; then
    log "Migrations completed successfully"
else
    error "Django migrations failed!"
    docker logs "$APP_SERVICE" | tail -50
    exit 1
fi

# ============================= FINAL SUCCESS ================================
echo
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                   DEPLOYMENT SUCCESSFUL!                         ║"
echo "║                                                                  ║"
echo "║   Enjoy        → https://$(echo "milky-way.space")               ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo

docker-compose ps --services | grep -E "(app|celery|db|redis|nginx)" | \
    xargs -I {} sh -c "echo '→ {}: '; docker-compose ps {} | tail -1"