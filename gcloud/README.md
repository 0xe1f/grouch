# Cloud Run Deployment

Deployment to Google Cloud Platform using Cloud Run.

## Components

- **app** — Cloud Run service running the Python/Flask application; TLS terminated by Cloud Run
- **couchdb** — Cloud Run service running CouchDB 3.5.1; internal ingress only, GCS-backed persistent volume, fixed at one instance
- **refresh-feeds** — Cloud Run Job that fetches new feed content, triggered every 10 minutes by Cloud Scheduler
- **compact-db** — Cloud Run Job that compacts the CouchDB database, triggered daily at 3 AM PT by Cloud Scheduler

> **Note:** CouchDB auto-compaction is disabled in the deployed configuration due to incompatibility with Cloud Storage FUSE staged writes. Compaction is handled exclusively by the `compact-db` scheduled job.

## Prerequisites

- `gcloud` CLI installed and authenticated (`gcloud auth login`)
- Docker installed locally (used to build and push images)
- GCP project with billing enabled

## Deployment

All infrastructure is provisioned and all services are deployed by a single script from the `gcloud/` directory:

```bash
# First deploy
PROJECT_ID=my-project REGION=us-west2 ./deploy.sh

# Subsequent deploys (app only; CouchDB skipped if already deployed)
PROJECT_ID=my-project REGION=us-west2 ./deploy.sh

# Force CouchDB rebuild and redeploy
PROJECT_ID=my-project REGION=us-west2 ./deploy.sh --redeploy-couchdb
```

`deploy.sh` is fully idempotent — safe to re-run at any time. It creates the following GCP resources if they do not already exist:

- Artifact Registry repository
- Serverless VPC Access connector
- Cloud Router and Cloud NAT (for outbound internet access from VPC-connected services)
- GCS bucket for CouchDB data
- Cloud Run services (`app`, `couchdb`)
- Cloud Run Jobs (`refresh-feeds`, `compact-db`)
- Cloud Scheduler jobs

### Deployment Order

CouchDB is always deployed before the app because the app image is built with the CouchDB service URL baked into its configuration. On subsequent runs, CouchDB is skipped unless `--redeploy-couchdb` is passed or `couchdb/generated/gcloud_creds.sh` contains no `COUCHDB_HOST`.

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `PROJECT_ID` | GCP project ID |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `REGION` | `us-central1` | GCP region for all resources |
| `AR_REPO` | `grouch` | Artifact Registry repository name |
| `GCS_BUCKET` | `grouch-couchdb-PROJECT_ID` | GCS bucket name for CouchDB persistent data |
| `VPC_CONNECTOR` | `grouch-connector` | Serverless VPC Access connector name |
| `HTTP_PORT` | `8080` | App container HTTP port |
| `GIT_REPO` | `https://github.com/0xe1f/grouch.git` | Source repository cloned into the app image |
| `GIT_BRANCH` | `master` | Branch or tag to clone |
| `COUCHDB_PORT` | `5984` | CouchDB container port |

### Cloud Run Runtime Variables

These are set automatically on the `app` Cloud Run service by `app/run.sh`. They do not need to be provided manually.

| Variable | Source |
|----------|--------|
| `GROUCH_DATABASE_NAME` | `app/generated/config.toml` |
| `GROUCH_DATABASE_HOST` | CouchDB Cloud Run service URL (from `couchdb/generated/gcloud_creds.sh`) |
| `GROUCH_DATABASE_PORT` | Always `443` (Cloud Run HTTPS) |
| `GROUCH_DATABASE_USERNAME` | CouchDB admin username |
| `GROUCH_DATABASE_PASSWORD` | CouchDB admin password |
| `GROUCH_SECRET_KEY` | `app/generated/config.toml` |

## Generated Files

These files are produced by the build and deploy scripts and are not committed to the repository.

| File | Description |
|------|-------------|
| `couchdb/generated/gcloud_creds.sh` | CouchDB admin credentials and service URL; preserved across rebuilds |
| `couchdb/generated/local.ini` | CouchDB config generated at build time (credentials, port, compaction settings) |
| `couchdb/generated/creds.sh` | Internal credentials file used by the container init script (`localhost` as host) |
| `app/generated/config.toml` | App config with database connection details and secret key |

## Scheduled Jobs

| Job | Schedule | Description |
|-----|----------|-------------|
| `refresh-feeds` | Every 10 minutes | Fetches new content for all subscribed feeds |
| `compact-db` | Daily at 3 AM PT | Compacts the CouchDB database to reclaim disk space |
