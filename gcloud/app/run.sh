#!/bin/bash

set -e

PROJECT_ID=${PROJECT_ID:?"PROJECT_ID is required"}
REGION=${REGION:-"us-central1"}
AR_REPO=${AR_REPO:-"grouch"}
HTTP_PORT=${HTTP_PORT:-8080}
VPC_CONNECTOR=${VPC_CONNECTOR:-"grouch-connector"}

IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/app"

# CouchDB connection credentials
. ../couchdb/generated/gcloud_creds.sh
COUCHDB_HOSTNAME=$(echo "$COUCHDB_HOST" | sed 's|https://||')
COUCHDB_EXTERNAL_PORT=443

# App-level secrets from generated config (SECRET_KEY, DATABASE_NAME)
if [ ! -f generated/config.toml ]; then
    echo "ERROR: generated/config.toml not found - run app/build.sh first" >&2
    exit 1
fi
SECRET_KEY=$(grep '^SECRET_KEY' generated/config.toml | sed 's/^SECRET_KEY *= *"\(.*\)"/\1/')
DATABASE_NAME=$(grep '^DATABASE_NAME' generated/config.toml | sed 's/^DATABASE_NAME *= *"\(.*\)"/\1/')
: ${SECRET_KEY:?"SECRET_KEY could not be read from generated/config.toml"}
: ${DATABASE_NAME:?"DATABASE_NAME could not be read from generated/config.toml"}

gcloud run deploy app \
    --image "$IMAGE" \
    --port "$HTTP_PORT" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --set-env-vars "\
GROUCH_DATABASE_NAME=$DATABASE_NAME,\
GROUCH_DATABASE_HOST=$COUCHDB_HOSTNAME,\
GROUCH_DATABASE_PORT=$COUCHDB_EXTERNAL_PORT,\
GROUCH_DATABASE_USERNAME=$COUCHDB_ADMIN_USER,\
GROUCH_DATABASE_PASSWORD=$COUCHDB_ADMIN_PASSWORD,\
GROUCH_SECRET_KEY=$SECRET_KEY" \
    --vpc-connector "$VPC_CONNECTOR" \
    --vpc-egress all-traffic \
    --allow-unauthenticated \
    "$@"
