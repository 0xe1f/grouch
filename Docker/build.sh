#!/bin/bash

set -e

NETWORK=${NETWORK:-"grouch"}
export NETWORK

cd couchdb; ./build.sh
cd ../app; ./build.sh
