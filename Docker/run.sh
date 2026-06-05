#!/bin/bash

set -e

NETWORK=${NETWORK:-"grouch"}
export NETWORK

docker network inspect $NETWORK >/dev/null 2>&1 || \
    docker network create $NETWORK

cd redis;      ./run.sh
cd ../couchdb; ./run.sh
cd ../app;     ./run.sh
cd ../worker;  ./run.sh
cd ../nginx;   ./run.sh
