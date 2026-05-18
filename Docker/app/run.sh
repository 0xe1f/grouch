#!/bin/bash

NETWORK=${NETWORK:-"grouch"}
NAME="app.$NETWORK"
IMAGE="$NETWORK/app"
HTTP_PORT=${HTTP_PORT:-8080}

(docker rm -f $NAME >/dev/null 2>&1 || true) && \
    (docker run --name $NAME -d \
        --network $NETWORK \
        --rm \
        $IMAGE \
        $@)
