#!/bin/bash

set -e

NETWORK=${NETWORK:-"grouch"}
export NETWORK

docker network inspect $NETWORK >/dev/null 2>&1 || \
    docker network create $NETWORK

cd couchdb; ./run.sh
sleep 5
cd ../app; ./run.sh
