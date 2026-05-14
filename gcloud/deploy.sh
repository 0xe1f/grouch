#!/bin/bash

set -e

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  --redeploy-couchdb    Force rebuild and redeploy of the CouchDB service
  -h, --help            Show this help message

Environment variables:
  PROJECT_ID            GCP project ID (required)
  REGION                Deployment region (default: us-central1)
  AR_REPO               Artifact Registry repository name (default: grouch)
  GCS_BUCKET            GCS bucket for CouchDB data (default: grouch-couchdb-PROJECT_ID)
  VPC_CONNECTOR         Serverless VPC connector name (default: grouch-connector)
EOF
}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID environment variable is required."
    echo
    usage
    exit 1
fi

REDEPLOY_COUCHDB=false
for arg in "$@"; do
    case $arg in
        --redeploy-couchdb) REDEPLOY_COUCHDB=true ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $arg"; usage; exit 1 ;;
    esac
done

export PROJECT_ID
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

echo "==> Provisioning refresh job and scheduler..."
IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/app"
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format 'value(projectNumber)')
SCHEDULER_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Enable Cloud Scheduler API
gcloud services enable cloudscheduler.googleapis.com --project "$PROJECT_ID"

# Grant compute SA permission to invoke Cloud Run jobs
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member "serviceAccount:$SCHEDULER_SA" \
    --role "roles/run.invoker"

# Create refresh-feeds Cloud Run Job if it doesn't exist
gcloud run jobs describe refresh-feeds \
    --region "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1 || \
gcloud run jobs create refresh-feeds \
    --image "$IMAGE" \
    --command "python3" \
    --args "refresh.py,-f,10" \
    --vpc-connector "$VPC_CONNECTOR" \
    --vpc-egress all-traffic \
    --region "$REGION" \
    --project "$PROJECT_ID"

# Create Cloud Scheduler job if it doesn't exist
gcloud scheduler jobs describe refresh-feeds-scheduler \
    --location "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1 || \
gcloud scheduler jobs create http refresh-feeds-scheduler \
    --location "$REGION" \
    --schedule "*/10 * * * *" \
    --uri "https://run.googleapis.com/v2/projects/$PROJECT_ID/locations/$REGION/jobs/refresh-feeds:run" \
    --message-body "{}" \
    --oauth-service-account-email "$SCHEDULER_SA" \
    --project "$PROJECT_ID"

echo "==> Provisioning compact-db job and scheduler..."

# Create compact-db Cloud Run Job if it doesn't exist
gcloud run jobs describe compact-db \
    --region "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1 || \
gcloud run jobs create compact-db \
    --image "$IMAGE" \
    --command "python3" \
    --args "gcloud/compact/compact.py" \
    --vpc-connector "$VPC_CONNECTOR" \
    --vpc-egress all-traffic \
    --task-timeout 30m \
    --region "$REGION" \
    --project "$PROJECT_ID"

# Create compact-db Cloud Scheduler job if it doesn't exist
gcloud scheduler jobs describe compact-db-scheduler \
    --location "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1 || \
gcloud scheduler jobs create http compact-db-scheduler \
    --location "$REGION" \
    --schedule "0 3 * * *" \
    --time-zone "America/Los_Angeles" \
    --uri "https://run.googleapis.com/v2/projects/$PROJECT_ID/locations/$REGION/jobs/compact-db:run" \
    --message-body "{}" \
    --oauth-service-account-email "$SCHEDULER_SA" \
    --project "$PROJECT_ID"
