#!/bin/bash

NETWORK=${NETWORK:-"grouch"}
NAME="app.$NETWORK"
IMAGE="$NETWORK/app"
HTTP_PORT=${HTTP_PORT:-8000}

docker run --name $NAME -d \
    --publish 8080:$HTTP_PORT \
    --network $NETWORK \
    --rm \
    $IMAGE
