#!/bin/bash

NETWORK=${NETWORK:-"grouch"}
NAME="nginx.$NETWORK"
IMAGE="$NETWORK/nginx"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SETTINGS="$SCRIPT_DIR/../../settings.toml"

DOMAIN=$(grep '^DOMAIN' "$SETTINGS" 2>/dev/null | cut -d= -f2- | tr -d ' "' | head -1)
LETSENCRYPT_EMAIL=$(grep '^LETSENCRYPT_EMAIL' "$SETTINGS" 2>/dev/null | cut -d= -f2- | tr -d ' "' | head -1)

# Repo-root cert takes priority over Let's Encrypt
CERT_SOURCE=""
[ -f "$SCRIPT_DIR/../../cert.pem" ] && [ -f "$SCRIPT_DIR/../../key.pem" ] && CERT_SOURCE="custom"

docker volume create letsencrypt >/dev/null 2>&1 || true

(docker rm -f $NAME >/dev/null 2>&1 || true) && \
    docker run --name $NAME -d \
    --publish 80:80 \
    --publish 443:443 \
    --network $NETWORK \
    --rm \
    -v letsencrypt:/etc/letsencrypt \
    ${CERT_SOURCE:+-e CERT_SOURCE="$CERT_SOURCE"} \
    ${DOMAIN:+-e DOMAIN="$DOMAIN"} \
    ${LETSENCRYPT_EMAIL:+-e LETSENCRYPT_EMAIL="$LETSENCRYPT_EMAIL"} \
    $IMAGE \
    $@
