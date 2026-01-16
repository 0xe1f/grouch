#!/bin/bash

NETWORK=${NETWORK:-"grouch"}
NAME="couchdb.$NETWORK"
IMAGE="$NETWORK/couchdb"
VOLUME="$NAME.vol"

docker volume inspect $VOLUME >/dev/null 2>&1 || \
    docker volume create $VOLUME >/dev/null

# FIXME!! user/password
ADMIN_USER=admin
ADMIN_PASSWORD=password

docker run --name $NAME -d \
    -e COUCHDB_USER=$ADMIN_USER \
    -e COUCHDB_PASSWORD=$ADMIN_PASSWORD \
    --network $NETWORK \
    --volume $VOLUME:/opt/couchdb/data \
    --rm \
    $IMAGE
