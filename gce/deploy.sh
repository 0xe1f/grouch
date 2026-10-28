#!/bin/bash

# Redeploy the grouch stack on an existing GCE VM.
# Syncs source and Docker/ from local, rebuilds images, and restarts containers.
# TLS certificates are preserved in the letsencrypt Docker volume on the VM.
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

if [ ! -f "$SCRIPT_DIR/settings.toml" ]; then
    echo "ERROR: gce/settings.toml not found. Copy settings.toml.example to gce/settings.toml and configure." >&2
    exit 1
fi

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

echo "==> Copying gce/settings.toml to Docker/ on VM"
_ssh "cp $REMOTE_HOME/grouch/gce/settings.toml $REMOTE_HOME/grouch/Docker/settings.toml"
_ssh "[ -f $REMOTE_HOME/grouch/gce/cert.pem ] && cp $REMOTE_HOME/grouch/gce/cert.pem $REMOTE_HOME/grouch/Docker/cert.pem || true"
_ssh "[ -f $REMOTE_HOME/grouch/gce/key.pem ]  && cp $REMOTE_HOME/grouch/gce/key.pem  $REMOTE_HOME/grouch/Docker/key.pem  || true"

# ---------------------------------------------------------------------------
echo "==> Stopping containers"
_ssh "
    for name in nginx.$NETWORK worker.$NETWORK app.$NETWORK couchdb.$NETWORK redis.$NETWORK; do
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

# Ensure Let's Encrypt renewal cron is present (idempotent). First-time setup
# installs this, but it was easy to lose if DOMAIN was added later or crontab
# was rewritten — deploy should keep it healthy.
DOMAIN=$(grep '^DOMAIN' "$SCRIPT_DIR/settings.toml" 2>/dev/null | cut -d= -f2- | tr -d ' "' | head -1)
if [ -n "$DOMAIN" ]; then
    echo "==> Ensuring Let's Encrypt renewal cron"
    CRON_CMD="docker exec nginx.$NETWORK /usr/local/bin/certbot-renew.sh >> /var/log/grouch-certbot.log 2>&1"
    _ssh "crontab -l 2>/dev/null | grep -qF '$CRON_CMD' || { crontab -l 2>/dev/null; echo '0 3 * * 1 $CRON_CMD'; } | crontab -"
fi

echo "==> Done."
