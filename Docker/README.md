# Docker Deployment

Local development and self-hosted deployment using Docker.

## Components

- **app** — Python/Flask web application served by gunicorn over HTTP (internal only)
- **couchdb** — CouchDB 3.5.1 database, accessible only within the Docker network
- **nginx** — Reverse proxy handling TLS termination, HTTP→HTTPS redirect, and WebSocket proxying

nginx is the only component that publishes ports to the host (80 and 443). The app container is internal to the Docker network.

## Prerequisites

- Docker
- `openssl` (used by `nginx/build.sh` to generate the self-signed TLS certificate)
- `envsubst` (part of `gettext`; used by `nginx/build.sh` to generate config)

## Quick Start

```bash
# From the repo root: create settings.toml from the example
cp settings.toml.example settings.toml
# Edit settings.toml as needed, then:

# From Docker/
./build.sh   # builds couchdb, app, then nginx
./run.sh     # creates docker network, starts couchdb, app, nginx
```

The app is available at `https://localhost`. HTTP requests on port 80 are redirected to HTTPS.

## Configuration

User-configurable settings live in `settings.toml` at the repo root (copy from `settings.toml.example`). The build scripts generate everything else automatically.

| Setting | Default | Description |
|---------|---------|-------------|
| `PERMANENT_SESSION_LIFETIME` | `2678400` | Session lifetime in seconds (31 days) |
| `REFRESH_INTERVAL_MINUTES` | `20` | Feed refresh interval in minutes |
| `BLOCK_NEW_ACCOUNTS` | `true` | Block new user registrations |
| `CORS_ALLOWED_ORIGINS` | `*` | Socket.IO allowed origins |
| `SECRET_KEY` | _(generated)_ | Flask secret key; set to persist sessions across rebuilds |

CouchDB credentials (`admin`/`password`) are defined in `couchdb/etc/local.ini`. To change them, edit that file and rebuild.

## Step-by-Step

### 1. Build CouchDB

```bash
cd couchdb && ./build.sh
```

Reads credentials and port from `couchdb/etc/local.ini` and builds the CouchDB image.

### 2. Build app

```bash
cd app && ./build.sh
```

Reads CouchDB credentials from `couchdb/etc/local.ini` and user settings from `settings.toml`, generates `app/generated/config.toml`, and builds the app image.

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

## Generated Files

These files are created by the build scripts and are not committed to the repository.

| File | Description |
|------|-------------|
| `app/generated/config.toml` | Full app config merged from `settings.toml` and `couchdb/etc/local.ini` |
| `app/generated/cron.tab` | Cron schedule derived from `REFRESH_INTERVAL_MINUTES` |
| `nginx/generated/cert.pem` | Self-signed TLS certificate; preserved across rebuilds |
| `nginx/generated/key.pem` | TLS private key; preserved across rebuilds |
| `nginx/generated/nginx.conf` | nginx config with network name and app port substituted |
