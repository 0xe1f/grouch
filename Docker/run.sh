#!/bin/bash

set -e

NETWORK=${NETWORK:-"grouch"}
export NETWORK

docker network inspect $NETWORK >/dev/null 2>&1 || \
    docker network create $NETWORK

cd couchdb; ./run.sh

echo "Waiting for CouchDB to be ready..."
until docker exec "couchdb.$NETWORK" curl -sf http://localhost:5984/_up >/dev/null 2>&1; do
    sleep 2
done

cd ../app; ./run.sh
cd ../nginx; ./run.sh
