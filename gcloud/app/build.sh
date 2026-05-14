#!/bin/bash

set -e

PROJECT_ID=${PROJECT_ID:?"PROJECT_ID is required"}
REGION=${REGION:-"us-central1"}
AR_REPO=${AR_REPO:-"grouch"}

HTTP_PORT=${HTTP_PORT:-8080}
GIT_REPO=${GIT_REPO:-"https://github.com/0xe1f/grouch.git"}
GIT_BRANCH=${GIT_BRANCH:-"master"}

IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/app"

. ../couchdb/generated/gcloud_creds.sh
mkdir -p generated

# Cloud Run serves CouchDB over HTTPS on port 443; strip the scheme from the URL
COUCHDB_HOSTNAME=$(echo "$COUCHDB_HOST" | sed 's|https://||')
COUCHDB_EXTERNAL_PORT=443

if [ -f generated/config.toml ]; then
    # Update CouchDB settings in existing config.toml
    cp generated/config.toml /tmp/config.toml
    sed \
        -e "s|^DATABASE_HOST .*|DATABASE_HOST = \"$COUCHDB_HOSTNAME\"|" \
        -e "s|^DATABASE_PORT .*|DATABASE_PORT = \"$COUCHDB_EXTERNAL_PORT\"|" \
        -e "s|^DATABASE_USERNAME .*|DATABASE_USERNAME = \"$COUCHDB_ADMIN_USER\"|" \
        -e "s|^DATABASE_PASSWORD .*|DATABASE_PASSWORD = \"$COUCHDB_ADMIN_PASSWORD\"|" \
        /tmp/config.toml > generated/config.toml
    rm -f /tmp/config.toml
else
    # Create new config.toml from defaults
    SECRET_KEY=`LC_ALL=C tr -dc 'A-Za-z0-9%_+;:,.-' </dev/urandom | head -c 64; echo`
    sed \
        -e "s|^#SECRET_KEY .*|SECRET_KEY = \"$SECRET_KEY\"|" \
        -e "s|^#DATABASE_HOST .*|DATABASE_HOST = \"$COUCHDB_HOSTNAME\"|" \
        -e "s|^#DATABASE_PORT .*|DATABASE_PORT = \"$COUCHDB_EXTERNAL_PORT\"|" \
        -e "s|^#DATABASE_USERNAME .*|DATABASE_USERNAME = \"$COUCHDB_ADMIN_USER\"|" \
        -e "s|^#DATABASE_PASSWORD .*|DATABASE_PASSWORD = \"$COUCHDB_ADMIN_PASSWORD\"|" \
        ../../Docker/app/etc/config.toml.default > generated/config.toml
fi

docker build \
    --platform linux/amd64 \
    --build-arg HTTP_PORT=$HTTP_PORT \
    --build-arg GIT_REPO=$GIT_REPO \
    --build-arg GIT_BRANCH=$GIT_BRANCH \
    -t $IMAGE . \
    "$@"

docker push $IMAGE
