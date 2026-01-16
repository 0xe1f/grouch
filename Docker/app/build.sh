#!/bin/bash

set -e

NETWORK=${NETWORK:-"grouch"}
NAME="app.$NETWORK"
IMAGE="$NETWORK/app"

COUCHDB_PORT=${COUCHDB_PORT:-5984}
HTTP_PORT=${HTTP_PORT:-8000}
GIT_REPO=${GIT_REPO:-"https://github.com/0xe1f/grouch.git"}
GIT_BRANCH=${GIT_BRANCH:-"master"}

. ../couchdb/generated/set_creds.sh
mkdir -p generated

echo "Generating config.toml from template..."
SECRET_KEY=`LC_ALL=C tr -dc 'A-Za-z0-9%_-+;:,.' </dev/urandom | head -c 64; echo`
sed \
    -e "s/^# SECRET_KEY .*/SECRET_KEY = \"$SECRET_KEY\"/" \
    -e "s/^DATABASE_HOST .*/DATABASE_HOST = \"$COUCHDB_HOST\"/" \
    -e "s/^DATABASE_PORT .*/DATABASE_PORT = \"$COUCHDB_PORT\"/" \
    -e "s/^DATABASE_USERNAME .*/DATABASE_USERNAME = \"$COUCHDB_ADMIN_USER\"/" \
    -e "s/^DATABASE_PASSWORD .*/DATABASE_PASSWORD = \"$COUCHDB_ADMIN_PASSWORD\"/" \
    -e "s/^# .*//" \
    -e "/^\s*$/d" \
    ../../config.toml.example > generated/config.toml

docker build \
    --build-arg HTTP_PORT=$HTTP_PORT \
    --build-arg GIT_REPO=$GIT_REPO \
    --build-arg GIT_BRANCH=$GIT_BRANCH \
    -t $IMAGE .
