#!/bin/bash

NETWORK=${NETWORK:-"grouch"}
NAME="couchdb.$NETWORK"
IMAGE="$NETWORK/couchdb"
VOLUME="$NAME.vol"

docker volume inspect $VOLUME >/dev/null 2>&1 || \
    docker volume create $VOLUME >/dev/null

(docker rm -f $NAME >/dev/null 2>&1 || true) && \
    (docker run --name $NAME -d \
        --network $NETWORK \
        --volume $VOLUME:/opt/couchdb/data \
        --rm \
        $IMAGE \
        $@)

echo "Waiting for CouchDB to be ready..."
until docker exec "$NAME" curl -sf http://localhost:5984/_up >/dev/null 2>&1; do
    sleep 2
done
