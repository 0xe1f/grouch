# Docker Deployment

Local development and self-hosted deployment using Docker.

## Components

- **app** — Python/Flask web application served by gunicorn over HTTP (internal only)
- **couchdb** — CouchDB 3.5.1 database with auto-generated admin credentials
- **nginx** — Reverse proxy handling TLS termination, HTTP→HTTPS redirect, and WebSocket proxying

nginx is the only component that publishes ports to the host (80 and 443). The app container is internal to the Docker network.

## Prerequisites

- Docker
- `openssl` (used by `nginx/build.sh` to generate the self-signed TLS certificate)
- `envsubst` (part of `gettext`; used by `nginx/build.sh` to generate config)

## Quick Start

```bash
# From Docker/
./build.sh   # builds couchdb, app, then nginx
./run.sh     # creates docker network, starts couchdb, app, nginx
```

The app is available at `https://localhost`. HTTP requests on port 80 are redirected to HTTPS.

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

### 3. Build nginx

```bash
cd nginx && ./build.sh
```

Generates a self-signed TLS certificate into `nginx/generated/` (preserved across rebuilds), substitutes the network name and app port into `nginx.conf`, and builds the nginx image.

### 4. Run CouchDB

```bash
cd couchdb && ./run.sh
```

Creates a named Docker volume for persistent data and starts the CouchDB container on the shared network.

### 5. Run app

```bash
cd app && ./run.sh
```

Starts the app container on the shared network. No host ports are published; all external access goes through nginx.

### 6. Run nginx

```bash
cd nginx && ./run.sh
```

Starts the nginx container, publishing ports 80 (HTTP redirect) and 443 (HTTPS proxy) on the host.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NETWORK` | `grouch` | Docker network name; also used as image and container name prefix |
| `HTTP_PORT` | `8080` | App internal HTTP port (not published to host) |
| `APP_PORT` | `8080` | Port nginx proxies to on the app container (should match `HTTP_PORT`) |
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
| `nginx/generated/cert.pem` | Self-signed TLS certificate; preserved across rebuilds |
| `nginx/generated/key.pem` | TLS private key; preserved across rebuilds |
| `nginx/generated/nginx.conf` | nginx config with network name and app port substituted |
