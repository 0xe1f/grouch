#!/bin/bash

NETWORK=${NETWORK:-"grouch"}
NAME="nginx.$NETWORK"
IMAGE="$NETWORK/nginx"

docker run --name $NAME -d \
    --publish 80:80 \
    --publish 443:443 \
    --network $NETWORK \
    --rm \
    $IMAGE \
    $@
