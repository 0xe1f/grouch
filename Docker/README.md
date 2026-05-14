# Docker Deployment

Local development and self-hosted deployment using Docker.

## Components

- **app** — Python/Flask web application served by gunicorn over HTTP and HTTPS
- **couchdb** — CouchDB 3.5.1 database with auto-generated admin credentials

## Prerequisites

- Docker
- `openssl` (for self-signed TLS certificate generation)

## Quick Start

```bash
# From Docker/
./build.sh   # builds couchdb, then app
./run.sh     # creates docker network, starts couchdb, starts app
```

The app is available at `http://localhost:8080` and `https://localhost:8443`.

## Step-by-Step

### 1. Build CouchDB

```bash
cd couchdb && ./build.sh
```

Generates random admin credentials into `couchdb/generated/creds.sh` (preserved across rebuilds) and produces `couchdb/generated/local.ini` with credentials and port baked in.

### 2. Build app

```bash
cd app && ./build.sh
```

Reads CouchDB credentials from `couchdb/generated/creds.sh`, generates a self-signed TLS certificate if one doesn't exist, and produces `app/generated/config.toml`. Builds the Docker image by cloning the source repository.

### 3. Run CouchDB

```bash
cd couchdb && ./run.sh
```

Creates a named Docker volume for persistent data and starts the CouchDB container on the shared network.

### 4. Run app

```bash
cd app && ./run.sh
```

Starts the app container, publishing HTTP on port 8080 and HTTPS on port 8443.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NETWORK` | `grouch` | Docker network name; also used as image and container name prefix |
| `HTTP_PORT` | `8080` | App HTTP port, published on the host |
| `HTTPS_PORT` | `8443` | App HTTPS port, published on the host |
| `GIT_REPO` | `https://github.com/0xe1f/grouch.git` | Source repository cloned into the app image |
| `GIT_BRANCH` | `master` | Branch or tag to clone |
| `COUCHDB_PORT` | `5984` | CouchDB listening port |

## Generated Files

These files are created by the build scripts and are not committed to the repository.

| File | Description |
|------|-------------|
| `couchdb/generated/creds.sh` | Random admin credentials; preserved across rebuilds |
| `couchdb/generated/local.ini` | CouchDB config with credentials and port baked in |
| `app/generated/config.toml` | App config with database connection details and secret key |
| `app/generated/cert.pem` | Self-signed TLS certificate |
| `app/generated/key.pem` | TLS private key |
