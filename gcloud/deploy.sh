#!/bin/bash

set -e

export PROJECT_ID=${PROJECT_ID:?"PROJECT_ID is required"}
export REGION=${REGION:-"us-central1"}
export AR_REPO=${AR_REPO:-"grouch"}
export GCS_BUCKET=${GCS_BUCKET:-"grouch-couchdb-$PROJECT_ID"}
export VPC_CONNECTOR=${VPC_CONNECTOR:-"grouch-connector"}

# Ensure Docker is configured to authenticate with Artifact Registry
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet

# Create Artifact Registry repository if it doesn't exist
gcloud artifacts repositories describe "$AR_REPO" \
    --location "$REGION" \
    --project "$PROJECT_ID" >/dev/null 2>&1 || \
gcloud artifacts repositories create "$AR_REPO" \
    --repository-format docker \
    --location "$REGION" \
    --project "$PROJECT_ID"

# Enable Serverless VPC Access API
gcloud services enable vpcaccess.googleapis.com --project "$PROJECT_ID"

# Create VPC connector if it doesn't exist
gcloud compute networks vpc-access connectors describe "$VPC_CONNECTOR" \
    --region "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1 || \
gcloud compute networks vpc-access connectors create "$VPC_CONNECTOR" \
    --region "$REGION" \
    --network default \
    --range 10.8.0.0/28 \
    --project "$PROJECT_ID"

# Create Cloud Router if it doesn't exist (required by Cloud NAT)
gcloud compute routers describe grouch-router \
    --region "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1 || \
gcloud compute routers create grouch-router \
    --network default \
    --region "$REGION" \
    --project "$PROJECT_ID"

# Create Cloud NAT if it doesn't exist (gives app outbound internet access via VPC)
gcloud compute routers nats describe grouch-nat \
    --router grouch-router \
    --region "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1 || \
gcloud compute routers nats create grouch-nat \
    --router grouch-router \
    --auto-allocate-nat-external-ips \
    --nat-all-subnet-ip-ranges \
    --region "$REGION" \
    --project "$PROJECT_ID"

REDEPLOY_COUCHDB=false
for arg in "$@"; do
    case $arg in
        --redeploy-couchdb) REDEPLOY_COUCHDB=true ;;
    esac
done

# Check if CouchDB has already been deployed (URL known)
COUCHDB_HOST=""
if [ -f couchdb/generated/gcloud_creds.sh ]; then
    . couchdb/generated/gcloud_creds.sh
fi

if [ -z "$COUCHDB_HOST" ] || [ "$REDEPLOY_COUCHDB" = true ]; then
    echo "==> Building and deploying CouchDB..."
    (cd couchdb && ./build.sh)
    (cd couchdb && ./run.sh)
else
    echo "==> CouchDB already deployed at $COUCHDB_HOST, skipping (use --redeploy-couchdb to force)."
fi

echo "==> Building and deploying app..."
(cd app && ./build.sh)
(cd app && ./run.sh)
