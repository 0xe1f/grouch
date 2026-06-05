#!/bin/bash

NETWORK=${NETWORK:-"grouch"}
NAME="redis.$NETWORK"

(docker rm -f $NAME >/dev/null 2>&1 || true) && \
    (docker run --name $NAME -d \
        --network $NETWORK \
        --rm \
        redis:7-alpine \
        $@)

echo "Waiting for Redis to be ready..."
until docker exec "$NAME" redis-cli ping >/dev/null 2>&1; do
    sleep 1
done
