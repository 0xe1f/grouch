#!/bin/bash

set -e

NETWORK=${NETWORK:-"grouch"}
IMAGE="$NETWORK/couchdb"

# Parse credentials and port from local.ini — single source of truth
ADMIN_LINE=$(grep -A50 '^\[admins\]' etc/local.ini | grep -m1 '^[^;[ ]')
COUCHDB_ADMIN_USER=$(echo "$ADMIN_LINE" | cut -d= -f1 | tr -d ' ')
COUCHDB_ADMIN_PASSWORD=$(echo "$ADMIN_LINE" | cut -d= -f2- | tr -d ' ')

COUCHDB_PORT=$(grep -A20 '^\[chttpd\]' etc/local.ini | grep -m1 '^port' | cut -d= -f2 | tr -d ' ')
COUCHDB_PORT=${COUCHDB_PORT:-5984}

docker build \
    --build-arg COUCHDB_ADMIN_USER="$COUCHDB_ADMIN_USER" \
    --build-arg COUCHDB_ADMIN_PASSWORD="$COUCHDB_ADMIN_PASSWORD" \
    --build-arg COUCHDB_PORT="$COUCHDB_PORT" \
    -t "$IMAGE" . \
    "$@"
