#!/bin/bash

set -e

NETWORK=${NETWORK:-"grouch"}
export NETWORK

docker network inspect $NETWORK >/dev/null 2>&1 || \
    docker network create $NETWORK

cd redis; ./run.sh

echo "Waiting for Redis to be ready..."
until docker exec "redis.$NETWORK" redis-cli ping >/dev/null 2>&1; do
    sleep 1
done

cd ../couchdb; ./run.sh

echo "Waiting for CouchDB to be ready..."
until docker exec "couchdb.$NETWORK" curl -sf http://localhost:5984/_up >/dev/null 2>&1; do
    sleep 2
done

cd ../app; ./run.sh
cd ../worker; ./run.sh
cd ../nginx; ./run.sh
