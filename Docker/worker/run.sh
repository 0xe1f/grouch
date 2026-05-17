#!/bin/bash

NETWORK=${NETWORK:-"grouch"}
NAME="worker.$NETWORK"
IMAGE="$NETWORK/app"

(docker rm -f $NAME >/dev/null 2>&1 || true) && \
    (docker run --name $NAME -d \
        --network $NETWORK \
        --rm \
        --entrypoint tini \
        $IMAGE \
        -- /etc/grouch/worker.sh \
        $@)
