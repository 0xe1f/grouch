#!/bin/bash

NETWORK=${NETWORK:-"grouch"}
NAME="app.$NETWORK"
IMAGE="$NETWORK/app"
HTTP_PORT=${HTTP_PORT:-8080}
HTTPS_PORT=${HTTPS_PORT:-8443}

docker run --name $NAME -d \
    --publish 8080:$HTTP_PORT \
    --publish 8443:$HTTPS_PORT \
    --network $NETWORK \
    --rm \
    $IMAGE
