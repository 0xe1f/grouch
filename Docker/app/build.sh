#!/bin/bash

set -e

NETWORK=${NETWORK:-"grouch"}
NAME="app.$NETWORK"
IMAGE="$NETWORK/app"

COUCHDB_NAME="couchdb.$NETWORK"
COUCHDB_PORT=${COUCHDB_PORT:-5984}
HTTP_PORT=${HTTP_PORT:-8000}
GIT_REPO=${GIT_REPO:-"https://github.com/0xe1f/grouch.git"}
GIT_BRANCH=${GIT_BRANCH:-"master"}

if [ ! -f config.toml ]; then
    echo "Generating config.toml from template..."
    RAND_STRING=`LC_ALL=C tr -dc 'A-Za-z0-9#%_-+;:,.' </dev/urandom | head -c 64; echo`
    sed \
        -e "s/^# SECRET_KEY .*/SECRET_KEY = \"$RAND_STRING\"/" \
        -e "s/^DATABASE_HOST .*/# DATABASE_HOST will autopopulate for docker builds/" \
        -e "s/^DATABASE_PORT .*/# DATABASE_PORT will autopopulate for docker builds/" \
        -e "s/^# .*//" \
        -e "/^\s*$/d" \
        ../../config.toml.example > config.toml
fi

docker build \
    --build-arg COUCHDB_HOST=$COUCHDB_NAME \
    --build-arg COUCHDB_PORT=$COUCHDB_PORT \
    --build-arg HTTP_PORT=$HTTP_PORT \
    --build-arg GIT_REPO=$GIT_REPO \
    --build-arg GIT_BRANCH=$GIT_BRANCH \
    -t $IMAGE .
