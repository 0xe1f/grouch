#!/bin/bash

set -e

PROJECT_ID=${PROJECT_ID:?"PROJECT_ID is required"}
REGION=${REGION:-"us-central1"}
AR_REPO=${AR_REPO:-"grouch"}
GCS_BUCKET=${GCS_BUCKET:-"grouch-couchdb-$PROJECT_ID"}
VPC_CONNECTOR=${VPC_CONNECTOR:-"grouch-connector"}

IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/couchdb"

. generated/gcloud_creds.sh

# Create GCS bucket if it doesn't exist (mirrors docker volume create)
gcloud storage buckets describe gs://$GCS_BUCKET \
    --project "$PROJECT_ID" >/dev/null 2>&1 || \
gcloud storage buckets create gs://$GCS_BUCKET \
    --location "$REGION" \
    --project "$PROJECT_ID"

gcloud run deploy couchdb \
    --image "$IMAGE" \
    --port "$COUCHDB_PORT" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --set-env-vars "\
COUCHDB_USER=$COUCHDB_ADMIN_USER,\
COUCHDB_PASSWORD=$COUCHDB_ADMIN_PASSWORD" \
    --add-volume "name=couchdb-data,type=cloud-storage,bucket=$GCS_BUCKET" \
    --add-volume-mount "volume=couchdb-data,mount-path=/opt/couchdb/data" \
    --vpc-connector "$VPC_CONNECTOR" \
    --min-instances 1 \
    --max-instances 1 \
    --ingress internal \
    --allow-unauthenticated \
    "$@"

# Capture the assigned service URL and patch it into gcloud_creds.sh
COUCHDB_HOST=$(gcloud run services describe couchdb \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --format 'value(status.url)')
sed -i '' "s|^COUCHDB_HOST=.*|COUCHDB_HOST=\"$COUCHDB_HOST\"|" generated/gcloud_creds.sh
