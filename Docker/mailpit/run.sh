#!/bin/bash

# Dev-only: starts Mailpit to capture outgoing emails locally.
# SMTP: localhost:1025  Web UI: http://localhost:8025

NETWORK=${NETWORK:-"grouch"}
NAME="mailpit.$NETWORK"
SMTP_PORT=${MAILPIT_SMTP_PORT:-1025}
UI_PORT=${MAILPIT_UI_PORT:-8025}

(docker rm -f $NAME >/dev/null 2>&1 || true) && \
    docker run --name "$NAME" -d \
        --network "$NETWORK" \
        -p "$SMTP_PORT:1025" \
        -p "$UI_PORT:8025" \
        --rm \
        axllent/mailpit
