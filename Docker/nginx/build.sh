#!/bin/bash

set -e

NETWORK=${NETWORK:-"grouch"}
APP_PORT=${APP_PORT:-8080}
IMAGE="$NETWORK/nginx"

mkdir -p generated

# Select the baked-in fallback certificate (used when DOMAIN is not set,
# or as the startup cert while certbot runs its ACME challenge).
# Priority: existing generated/ certs → repo-root cert.pem/key.pem → autogenerate self-signed.
if [ -f generated/cert.pem ] && [ -f generated/key.pem ]; then
    echo "Using existing certificate in generated/."
elif [ -f "../cert.pem" ] && [ -f "../key.pem" ]; then
    echo "Copying certificate from Docker/..."
    cp ../cert.pem generated/cert.pem
    cp ../key.pem  generated/key.pem
else
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
