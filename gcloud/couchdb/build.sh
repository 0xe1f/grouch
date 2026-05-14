#!/bin/bash

set -e

PROJECT_ID=${PROJECT_ID:?"PROJECT_ID is required"}
REGION=${REGION:-"us-central1"}
AR_REPO=${AR_REPO:-"grouch"}

IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/couchdb"

COUCHDB_PORT=${COUCHDB_PORT:-5984}

mkdir -p generated

if [ ! -f generated/gcloud_creds.sh ]; then
    # Generate random admin username and password
    COUCHDB_ADMIN_USER=`LC_ALL=C tr -dc 'A-Za-z' </dev/urandom | head -c 8; echo`
    COUCHDB_ADMIN_PASSWORD=`LC_ALL=C tr -dc 'A-Za-z0-9%_+;:.-' </dev/urandom | head -c 16; echo`

    # Cloud Run service URL is not yet known; will be patched by run.sh after first deploy
    COUCHDB_HOST=""

    echo "#!/bin/bash" > generated/gcloud_creds.sh
    echo "COUCHDB_HOST=\"$COUCHDB_HOST\"" >> generated/gcloud_creds.sh
    echo "COUCHDB_PORT=\"$COUCHDB_PORT\"" >> generated/gcloud_creds.sh
    echo "COUCHDB_ADMIN_USER=\"$COUCHDB_ADMIN_USER\"" >> generated/gcloud_creds.sh
    echo "COUCHDB_ADMIN_PASSWORD=\"$COUCHDB_ADMIN_PASSWORD\"" >> generated/gcloud_creds.sh
else
    . generated/gcloud_creds.sh
fi

# Update local.ini with credentials and port
sed \
    -e "s/^;admin = .*/$COUCHDB_ADMIN_USER = $COUCHDB_ADMIN_PASSWORD/" \
    -e "s/^;port = .*/port = $COUCHDB_PORT/" \
    ../../Docker/couchdb/etc/local.ini.default > generated/local.ini

# Disable auto-compaction (incompatible with gcsfuse staged writes)
cat >> generated/local.ini << 'EOF'

[compaction_daemon]
check_interval = 999999999
EOF

# Generate creds.sh for init_db.sh (uses localhost since it runs inside the container)
echo "#!/bin/bash" > generated/creds.sh
echo "COUCHDB_HOST=\"localhost\"" >> generated/creds.sh
echo "COUCHDB_PORT=\"$COUCHDB_PORT\"" >> generated/creds.sh
echo "COUCHDB_ADMIN_USER=\"$COUCHDB_ADMIN_USER\"" >> generated/creds.sh
echo "COUCHDB_ADMIN_PASSWORD=\"$COUCHDB_ADMIN_PASSWORD\"" >> generated/creds.sh

docker build \
    --platform linux/amd64 \
    --build-arg COUCHDB_PORT=$COUCHDB_PORT \
    -t $IMAGE \
    . \
    "$@"

docker push $IMAGE
