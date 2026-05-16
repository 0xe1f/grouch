#!/bin/bash

NETWORK=${NETWORK:-"grouch"}
NAME="couchdb.$NETWORK"
IMAGE="$NETWORK/couchdb"
VOLUME="$NAME.vol"

docker volume inspect $VOLUME >/dev/null 2>&1 || \
    docker volume create $VOLUME >/dev/null

(docker stop $NAME >/dev/null 2>&1 || true) && \
    (docker rm $NAME >/dev/null 2>&1 || true) && \
    (docker run --name $NAME -d \
        --network $NETWORK \
        --volume $VOLUME:/opt/couchdb/data \
        --rm \
        $IMAGE \
        $@)
