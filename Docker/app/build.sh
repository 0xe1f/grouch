#!/bin/bash

set -e

NETWORK=${NETWORK:-"grouch"}
NAME="app.$NETWORK"
IMAGE="$NETWORK/app"

HTTP_PORT=${HTTP_PORT:-8080}
GIT_HASH=${GIT_HASH:-$(git -C ../.. rev-parse --short HEAD 2>/dev/null || echo "dev")}
BUILD_DATE=$(date -u +%Y-%m-%d)

. ../couchdb/generated/creds.sh
mkdir -p generated

if [ -f generated/config.toml ]; then
    # Update CouchDB settings in existing config.toml
    cp generated/config.toml /tmp/config.toml
    sed \
        -e "s/^DATABASE_HOST .*/DATABASE_HOST = \"$COUCHDB_HOST\"/" \
        -e "s/^DATABASE_PORT .*/DATABASE_PORT = \"$COUCHDB_PORT\"/" \
        -e "s/^DATABASE_USERNAME .*/DATABASE_USERNAME = \"$COUCHDB_ADMIN_USER\"/" \
        -e "s/^DATABASE_PASSWORD .*/DATABASE_PASSWORD = \"$COUCHDB_ADMIN_PASSWORD\"/" \
        /tmp/config.toml > generated/config.toml
    rm -f /tmp/config.toml
else
    # Create new config.toml from defaults
    SECRET_KEY=`LC_ALL=C tr -dc 'A-Za-z0-9%_+;:,.-' </dev/urandom | head -c 64; echo`
    sed \
        -e "s/^#SECRET_KEY .*/SECRET_KEY = \"$SECRET_KEY\"/" \
        -e "s/^#DATABASE_HOST .*/DATABASE_HOST = \"$COUCHDB_HOST\"/" \
        -e "s/^#DATABASE_PORT .*/DATABASE_PORT = \"$COUCHDB_PORT\"/" \
        -e "s/^#DATABASE_USERNAME .*/DATABASE_USERNAME = \"$COUCHDB_ADMIN_USER\"/" \
        -e "s/^#DATABASE_PASSWORD .*/DATABASE_PASSWORD = \"$COUCHDB_ADMIN_PASSWORD\"/" \
        etc/config.toml.default > generated/config.toml
fi

docker build \
    --build-arg HTTP_PORT=$HTTP_PORT \
    --build-arg GIT_HASH=$GIT_HASH \
    --build-arg BUILD_DATE=$BUILD_DATE \
    -f Dockerfile \
    -t $IMAGE \
    ../.. \
    $@
