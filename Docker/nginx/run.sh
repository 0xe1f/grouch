#!/bin/bash

NETWORK=${NETWORK:-"grouch"}
NAME="nginx.$NETWORK"
IMAGE="$NETWORK/nginx"

(docker rm -f $NAME >/dev/null 2>&1 || true) && \
    (docker run --name $NAME -d \
    --publish 80:80 \
    --publish 443:443 \
    --network $NETWORK \
    --rm \
    $IMAGE \
    $@)
