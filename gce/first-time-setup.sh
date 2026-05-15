#!/bin/bash

# Provision a GCE VM and deploy the full grouch stack (couchdb + app + nginx)
# using the existing Docker/ scripts. CouchDB data is stored on a Persistent
# Disk attached to the VM, avoiding the GCS FUSE reliability issues of the
# Cloud Run setup.
#
# Usage (from repo root or gce/):
#   PROJECT_ID=my-project ./gce/first-time-setup.sh
#
# See gce/README.md for full documentation.

set -e

PROJECT_ID=${PROJECT_ID:?"PROJECT_ID is required"}
ZONE=${ZONE:-"us-central1-a"}
REGION="${ZONE%-*}"
VM_NAME=${VM_NAME:-"grouch-server"}
MACHINE_TYPE=${MACHINE_TYPE:-"e2-small"}
DISK_NAME=${DISK_NAME:-"grouch-couchdb-data"}
DISK_SIZE=${DISK_SIZE:-"10GB"}
DISK_DEVICE="couchdb-data"
STATIC_IP_NAME=${STATIC_IP_NAME:-"grouch-ip"}
NETWORK_TAG="grouch-server"
NETWORK=${NETWORK:-"grouch"}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOCKER_DIR="$SCRIPT_DIR/../Docker"

_ssh() {
    gcloud compute ssh "$VM_NAME" \
        --zone "$ZONE" \
        --project "$PROJECT_ID" \
        --command "$1"
}

# ---------------------------------------------------------------------------
echo "==> Reserving static external IP: $STATIC_IP_NAME"
gcloud compute addresses describe "$STATIC_IP_NAME" \
    --region "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1 || \
gcloud compute addresses create "$STATIC_IP_NAME" \
    --region "$REGION" \
    --project "$PROJECT_ID"

EXTERNAL_IP=$(gcloud compute addresses describe "$STATIC_IP_NAME" \
    --region "$REGION" --project "$PROJECT_ID" \
    --format "value(address)")
echo "    $EXTERNAL_IP"

# ---------------------------------------------------------------------------
echo "==> Creating Persistent Disk: $DISK_NAME ($DISK_SIZE, pd-standard)"
gcloud compute disks describe "$DISK_NAME" \
    --zone "$ZONE" --project "$PROJECT_ID" >/dev/null 2>&1 || \
gcloud compute disks create "$DISK_NAME" \
    --zone "$ZONE" \
    --size "$DISK_SIZE" \
    --type pd-standard \
    --project "$PROJECT_ID"

# ---------------------------------------------------------------------------
echo "==> Creating firewall rule: allow-grouch-http (ports 80, 443)"
gcloud compute firewall-rules describe allow-grouch-http \
    --project "$PROJECT_ID" >/dev/null 2>&1 || \
gcloud compute firewall-rules create allow-grouch-http \
    --direction INGRESS \
    --action allow \
    --rules tcp:80,tcp:443 \
    --target-tags "$NETWORK_TAG" \
    --project "$PROJECT_ID"

# ---------------------------------------------------------------------------
echo "==> Creating VM: $VM_NAME ($MACHINE_TYPE, $ZONE)"
gcloud compute instances describe "$VM_NAME" \
    --zone "$ZONE" --project "$PROJECT_ID" >/dev/null 2>&1 || \
gcloud compute instances create "$VM_NAME" \
    --zone "$ZONE" \
    --machine-type "$MACHINE_TYPE" \
    --image-family debian-12 \
    --image-project debian-cloud \
    --disk "name=$DISK_NAME,device-name=$DISK_DEVICE,auto-delete=no" \
    --address "$EXTERNAL_IP" \
    --tags "$NETWORK_TAG" \
    --project "$PROJECT_ID"

# ---------------------------------------------------------------------------
echo "==> Waiting for SSH to become available..."
for i in $(seq 1 30); do
    _ssh "echo ok" >/dev/null 2>&1 && break || true
    echo "    ($i/30) retrying in 10s..."
    sleep 10
done

# ---------------------------------------------------------------------------
echo "==> Installing Docker"
_ssh "
    if command -v docker >/dev/null 2>&1; then
        echo '    Already installed'
    else
        set -e
        sudo apt-get update -qq
        sudo apt-get install -y -qq ca-certificates curl
        sudo install -m 0755 -d /etc/apt/keyrings
        sudo curl -fsSL https://download.docker.com/linux/debian/gpg \
            -o /etc/apt/keyrings/docker.asc
        sudo chmod a+r /etc/apt/keyrings/docker.asc
        . /etc/os-release
        echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
            https://download.docker.com/linux/debian \$VERSION_CODENAME stable\" | \
            sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
        sudo apt-get update -qq
        sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io
        sudo usermod -aG docker \$USER
        echo '    Installed'
    fi
"

# ---------------------------------------------------------------------------
echo "==> Mounting Persistent Disk at /mnt/couchdb-data"
# gcloud compute ssh opens a fresh connection each time, so the docker group
# membership added above is now active.
_ssh "
    set -e
    DEVICE=/dev/disk/by-id/google-$DISK_DEVICE
    sudo mkdir -p /mnt/couchdb-data
    if ! sudo blkid \$DEVICE 2>/dev/null | grep -q ext4; then
        echo '    Formatting disk ext4...'
        sudo mkfs.ext4 -F \$DEVICE
    fi
    if ! mountpoint -q /mnt/couchdb-data; then
        sudo mount \$DEVICE /mnt/couchdb-data
    fi
    if ! grep -q '$DISK_DEVICE' /etc/fstab; then
        echo \"\$DEVICE /mnt/couchdb-data ext4 defaults 0 2\" | sudo tee -a /etc/fstab
    fi
    sudo chown \$USER:\$USER /mnt/couchdb-data
    echo '    Mounted'
"

# ---------------------------------------------------------------------------
# Resolve the remote home directory explicitly — gcloud compute scp does not
# reliably expand ~/ in the destination path.
REMOTE_HOME=$(_ssh "echo \$HOME" | tr -d '\r')
echo "==> Syncing Docker/ to VM ($REMOTE_HOME/grouch/Docker/)"
_ssh "mkdir -p $REMOTE_HOME/grouch"
gcloud compute scp --recurse --compress \
    "$DOCKER_DIR" "$VM_NAME:$REMOTE_HOME/grouch/" \
    --zone "$ZONE" --project "$PROJECT_ID"

# ---------------------------------------------------------------------------
echo "==> Building Docker images on VM"
_ssh "
    set -e
    cd $REMOTE_HOME/grouch/Docker
    NETWORK=$NETWORK ./build.sh
"

# ---------------------------------------------------------------------------
# Pre-create the CouchDB named volume as a bind mount pointing to the
# Persistent Disk. Docker/couchdb/run.sh skips volume creation when the
# volume already exists, so CouchDB data lands on the Persistent Disk.
echo "==> Creating CouchDB Docker volume on Persistent Disk"
_ssh "
    set -e
    VOLUME=couchdb.$NETWORK.vol
    if docker volume inspect \$VOLUME >/dev/null 2>&1; then
        echo '    Volume already exists'
    else
        docker volume create --driver local \
            --opt type=none --opt o=bind \
            --opt device=/mnt/couchdb-data \
            \$VOLUME
        echo '    Volume created'
    fi
"

# ---------------------------------------------------------------------------
echo "==> Starting containers"
_ssh "
    set -e
    cd $REMOTE_HOME/grouch/Docker
    NETWORK=$NETWORK ./run.sh
"

# ---------------------------------------------------------------------------
# refresh-feeds runs as a Docker one-shot using the app image, matching the
# behaviour of the former Cloud Run Job (python3 refresh.py -f 10).
echo "==> Setting up cron: refresh-feeds (every 10 minutes)"
_ssh "
    CRON_CMD=\"*/10 * * * * docker run --rm --network $NETWORK $NETWORK/app python3 refresh.py -f 10 >> /var/log/grouch-refresh.log 2>&1\"
    ( crontab -l 2>/dev/null | grep -v 'refresh.py'; echo \"\$CRON_CMD\" ) | crontab -
    echo '    Cron job set'
"

# ---------------------------------------------------------------------------
echo ""
echo "========================================================"
echo " Deployment complete!"
echo "  External IP : $EXTERNAL_IP"
echo "  App URL     : https://$EXTERNAL_IP"
echo ""
echo " The app uses a self-signed TLS certificate."
echo " Browser security warnings are expected until you install"
echo " a real certificate. See gce/README.md for Certbot setup."
echo "========================================================"
