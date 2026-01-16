#!/bin/bash

NETWORK=${NETWORK:-"grouch"}
IMAGE="$NETWORK/couchdb"

COUCHDB_PORT=${COUCHDB_PORT:-5984}

docker build \
    --build-arg COUCHDB_PORT=$COUCHDB_PORT \
    -t $IMAGE .
