#!/bin/bash

# Redeploy the grouch stack on an existing GCE VM.
# Syncs Docker/ from local, rebuilds images, and restarts containers.
# Generated files (credentials, TLS certs) are preserved via the sync.
#
# Usage (from repo root or gce/):
#   PROJECT_ID=my-project ./gce/deploy.sh

set -e

PROJECT_ID=${PROJECT_ID:?"PROJECT_ID is required"}
ZONE=${ZONE:-"us-central1-a"}
VM_NAME=${VM_NAME:-"grouch-server"}
NETWORK=${NETWORK:-"grouch"}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/.."
DOCKER_DIR="$SCRIPT_DIR/../Docker"

GIT_HASH=$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo "dev")

_ssh() {
    gcloud compute ssh "$VM_NAME" \
        --zone "$ZONE" \
        --project "$PROJECT_ID" \
        --command "$1"
}

# ---------------------------------------------------------------------------
REMOTE_HOME=$(_ssh "echo \$HOME" | tr -d '\r')

echo "==> Syncing source to VM ($REMOTE_HOME/grouch/)"
tar -czf - \
    --exclude='./.git' \
    --exclude='./venv' \
    --exclude='./__pycache__' \
    --exclude='./config.toml' \
    --exclude='*.pyc' \
    -C "$REPO_ROOT" . | \
gcloud compute ssh "$VM_NAME" \
    --zone "$ZONE" --project "$PROJECT_ID" \
    --command "mkdir -p $REMOTE_HOME/grouch && tar -xzf - -C $REMOTE_HOME/grouch --warning=no-unknown-keyword"

echo "==> Syncing Docker/ to VM ($REMOTE_HOME/grouch/Docker/)"
gcloud compute scp --recurse --compress \
    "$DOCKER_DIR" "$VM_NAME:$REMOTE_HOME/grouch/" \
    --zone "$ZONE" --project "$PROJECT_ID"

# ---------------------------------------------------------------------------
echo "==> Stopping containers"
_ssh "
    for name in nginx.$NETWORK app.$NETWORK couchdb.$NETWORK; do
        docker stop \$name 2>/dev/null && echo \"    Stopped \$name\" || true
    done
"

# ---------------------------------------------------------------------------
echo "==> Rebuilding Docker images"
_ssh "
    set -e
    cd $REMOTE_HOME/grouch/Docker
    GIT_HASH=$GIT_HASH NETWORK=$NETWORK ./build.sh
"

# ---------------------------------------------------------------------------
echo "==> Starting containers"
_ssh "
    set -e
    cd $REMOTE_HOME/grouch/Docker
    NETWORK=$NETWORK ./run.sh
"

echo "==> Done."
