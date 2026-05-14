#!/bin/bash

set -e

NETWORK=${NETWORK:-"grouch"}
APP_PORT=${APP_PORT:-8080}
IMAGE="$NETWORK/nginx"

mkdir -p generated

# Generate self-signed TLS certificate if not already present
if [ ! -f generated/key.pem ] || [ ! -f generated/cert.pem ]; then
    echo "Generating new self-signed certificate and key..."
    openssl req \
        -x509 \
        -newkey rsa:4096 \
        -keyout generated/key.pem \
        -out generated/cert.pem \
        -sha256 \
        -days 365 \
        -nodes \
        -subj "/C=??/ST=??/L=??/O=??/OU=??/CN=Grouch Self-signed"
fi

# Substitute NETWORK and APP_PORT into nginx.conf; nginx variables ($host etc.) are left unchanged
export NETWORK APP_PORT
envsubst '${NETWORK} ${APP_PORT}' < nginx.conf > generated/nginx.conf

docker build -t $IMAGE . $@
