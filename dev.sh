#!/bin/bash

# Development launcher: starts CouchDB + Redis with localhost ports exposed,
# then runs serve.py with hot-reloading enabled.

set -e

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
NETWORK=${NETWORK:-"grouch"}
COUCHDB_CONTAINER="couchdb.$NETWORK"
REDIS_CONTAINER="redis.$NETWORK"
COUCHDB_PORT=5984
REDIS_PORT=6379

port_open() {
    nc -z -w1 localhost "$1" 2>/dev/null
}

# Ensure Docker network exists
docker network inspect "$NETWORK" >/dev/null 2>&1 || docker network create "$NETWORK" >/dev/null

# --- CouchDB ---
if port_open $COUCHDB_PORT; then
    echo "CouchDB already accessible on localhost:$COUCHDB_PORT — skipping restart."
else
    echo "Starting CouchDB (port $COUCHDB_PORT)..."
    docker rm -f "$COUCHDB_CONTAINER" 2>/dev/null || true

    VOLUME="$COUCHDB_CONTAINER.vol"
    docker volume inspect "$VOLUME" >/dev/null 2>&1 || docker volume create "$VOLUME" >/dev/null

    docker run --name "$COUCHDB_CONTAINER" -d \
        --network "$NETWORK" \
        --volume "$VOLUME:/opt/couchdb/data" \
        -p "$COUCHDB_PORT:$COUCHDB_PORT" \
        --rm \
        grouch/couchdb

    echo -n "Waiting for CouchDB"
    until curl -sf "http://localhost:$COUCHDB_PORT/_up" >/dev/null 2>&1; do
        sleep 1; echo -n "."; done
    echo " ready."
fi

# --- Redis ---
if port_open $REDIS_PORT; then
    echo "Redis already accessible on localhost:$REDIS_PORT — skipping restart."
else
    echo "Starting Redis (port $REDIS_PORT)..."
    docker rm -f "$REDIS_CONTAINER" 2>/dev/null || true

    docker run --name "$REDIS_CONTAINER" -d \
        --network "$NETWORK" \
        -p "$REDIS_PORT:$REDIS_PORT" \
        --rm \
        redis:7-alpine

    echo -n "Waiting for Redis"
    until docker exec "$REDIS_CONTAINER" redis-cli ping >/dev/null 2>&1; do
        sleep 1; echo -n "."; done
    echo " ready."
fi

# Parse CouchDB credentials from local.ini (single source of truth)
LOCAL_INI="$SCRIPT_DIR/Docker/couchdb/etc/local.ini"
ADMIN_LINE=$(grep -A50 '^\[admins\]' "$LOCAL_INI" | grep -m1 '^[^;[ ]')
COUCHDB_USER=$(echo "$ADMIN_LINE" | cut -d= -f1 | tr -d ' ')
COUCHDB_PASS=$(echo "$ADMIN_LINE" | cut -d= -f2- | tr -d ' ')

cd "$SCRIPT_DIR"
source venv/bin/activate
export PYTHONPATH="$SCRIPT_DIR"

# Override config.toml values to point at localhost services
export GROUCH_DATABASE_HOSTNAME=localhost
export GROUCH_DATABASE_PORT=$COUCHDB_PORT
export GROUCH_DATABASE_USERNAME=$COUCHDB_USER
export GROUCH_DATABASE_PASSWORD=$COUCHDB_PASS
export GROUCH_REDIS_URL="redis://localhost:$REDIS_PORT/0"

export FLASK_DEBUG=1

cleanup() {
    echo ""
    echo "Shutting down..."
    kill "$WORKER_PID" 2>/dev/null
    wait "$WORKER_PID" 2>/dev/null
}
trap cleanup EXIT INT TERM

echo ""
echo "Starting Celery worker..."
celery -A tasks.celery_app worker --loglevel=info --concurrency=2 &
WORKER_PID=$!

echo ""
echo "Starting serve.py with hot-reloading..."
exec python web/serve.py
