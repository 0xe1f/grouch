#!/bin/bash

NETWORK=${NETWORK:-"grouch"}
NAME="app.$NETWORK"
IMAGE="$NETWORK/app"
HTTP_PORT=${HTTP_PORT:-8080}

(docker stop $NAME >/dev/null 2>&1 || true) && \
    (docker rm $NAME >/dev/null 2>&1 || true) && \
    (docker run --name $NAME -d \
        --network $NETWORK \
        --rm \
        -e GROUCH_CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS:-"*"} \
        $IMAGE \
        $@)
