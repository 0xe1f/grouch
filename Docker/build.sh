#!/bin/bash

set -e

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
SETTINGS="$SCRIPT_DIR/settings.toml"

if [ ! -f "$SETTINGS" ]; then
    echo "ERROR: settings.toml not found. Copy settings.toml.example to Docker/settings.toml and configure." >&2
    exit 1
fi

NETWORK=${NETWORK:-"grouch"}
export NETWORK

cd "$SCRIPT_DIR/couchdb"; ./build.sh
cd "$SCRIPT_DIR/app"; ./build.sh
cd "$SCRIPT_DIR/nginx"; ./build.sh
