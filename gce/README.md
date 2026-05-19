# GCE Deployment

Deploys the full grouch stack (CouchDB + app + nginx) to a single Google Compute Engine VM using the existing `Docker/` scripts. CouchDB data is stored on a Persistent Disk, which gives it a real block-device filesystem and eliminates the stale-file-handle crashes caused by the Cloud Run + GCS FUSE setup.

## Components

| Component | Where it runs |
|-----------|--------------|
| **couchdb** | Docker container; data on a Persistent Disk (`/mnt/couchdb-data`) |
| **app** | Docker container (internal network only) |
| **nginx** | Docker container; publishes ports 80 and 443 to the host |
| **refresh-feeds** | Cron job on the VM (`*/10 * * * *`), runs the app image |

CouchDB auto-compaction works correctly on a Persistent Disk — no `compact-db` job is needed.

## Prerequisites

- `gcloud` CLI installed and authenticated (`gcloud auth login`)
- Docker installed locally (to build images for the initial credential/cert generation — actually, images are built on the VM; you only need the local `Docker/` scripts to run `build.sh` for credential generation if desired, but `deploy.sh` handles everything remotely)
- GCP project with billing enabled

## First Deploy

```bash
# From the gce/ directory: create settings.toml from the example
cp ../settings.toml.example settings.toml
# Edit settings.toml as needed, then:

PROJECT_ID=my-project ./first-time-setup.sh

# Override region/zone (default: us-central1-a)
PROJECT_ID=my-project ZONE=us-west1-b ./first-time-setup.sh
```

`first-time-setup.sh` is fully idempotent — safe to re-run. It creates the following GCP resources if they do not already exist:

- Static external IP address (`grouch-ip`)
- Persistent Disk for CouchDB data (`grouch-couchdb-data`, 10 GB pd-standard)
- Firewall rule allowing ports 80 and 443 (`allow-grouch-http`)
- VM running Debian 12 with Docker installed (`grouch-server`, `e2-small`)

After provisioning, it syncs `Docker/` to the VM, builds images, starts containers, and sets up the refresh-feeds cron job.

## Subsequent Deploys

```bash
PROJECT_ID=my-project ./deploy.sh
```

Syncs `Docker/` to the VM (preserving generated credentials and certs), rebuilds images, and restarts containers. CouchDB data on the Persistent Disk is never touched.

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `PROJECT_ID` | GCP project ID |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `ZONE` | `us-central1-a` | GCP zone for the VM and disk |
| `VM_NAME` | `grouch-server` | Compute Engine instance name |
| `MACHINE_TYPE` | `e2-small` | VM machine type |
| `DISK_NAME` | `grouch-couchdb-data` | Persistent Disk name |
| `DISK_SIZE` | `10GB` | Persistent Disk size (increase if needed) |
| `STATIC_IP_NAME` | `grouch-ip` | Name for the reserved external IP |
| `NETWORK` | `grouch` | Docker network / image name prefix |

## TLS Certificate

On first deploy, nginx uses a self-signed certificate. To supply your own certificate instead of using Let's Encrypt, place `cert.pem` and `key.pem` in `gce/` — they will be copied to the VM automatically and certbot will not be invoked.

To use a real Let's Encrypt certificate, set `DOMAIN` (and optionally `LETSENCRYPT_EMAIL`) in `gce/settings.toml` before deploying:

```toml
DOMAIN = "your.domain.com"
LETSENCRYPT_EMAIL = "admin@your.domain.com"
```

With `DOMAIN` set:

- `gce/first-time-setup.sh` reserves a static IP address. Point your domain's DNS A record at that IP before or after the initial deploy.
- The nginx container runs certbot automatically at startup using the ACME webroot challenge. If DNS is already propagated when the container first starts, the certificate is issued immediately.
- If the certificate cannot be obtained yet (DNS not propagated, port 80 not reachable), nginx falls back to the self-signed certificate and logs a warning. Once the issue is resolved, restart nginx to retry:

  ```bash
  gcloud compute ssh grouch-server --zone us-central1-a --project my-project \
    --command 'cd ~/grouch/Docker/nginx && ./run.sh'
  ```

- Certificates are stored in a Docker volume (`letsencrypt`) on the VM and survive image rebuilds — no re-issuance happens on every deploy.

- `gce/first-time-setup.sh` installs a weekly renewal cron job on the VM (`0 3 * * 1`). Renewal runs inside the nginx container via `docker exec` with no downtime.

## SSH Access

```bash
gcloud compute ssh grouch-server --zone us-central1-a --project my-project
```

## Useful Commands on the VM

```bash
# View running containers
docker ps

# Tail app logs
docker logs -f app.grouch

# Tail refresh-feeds cron output
tail -f /var/log/grouch-refresh.log

# Restart a single container
docker restart nginx.grouch

# Restart everything
cd ~/grouch/Docker && NETWORK=grouch ./run.sh
```

## Backups

The Persistent Disk can be snapshotted without stopping the VM:

```bash
gcloud compute disks snapshot grouch-couchdb-data \
    --zone us-central1-a \
    --snapshot-names grouch-couchdb-$(date +%Y%m%d) \
    --project my-project
```

Add this to a Cloud Scheduler job or a cron entry on the VM for automated daily backups.

## Differences from the Cloud Run Setup

| | Cloud Run + GCS FUSE | GCE VM |
|---|---|---|
| CouchDB storage | GCS FUSE (unreliable for DBs) | Persistent Disk (block device) |
| TLS | Managed by Cloud Run | Self-signed (or Certbot) |
| refresh-feeds | Cloud Run Job + Cloud Scheduler | Cron job on VM |
| compact-db | Cloud Run Job (workaround for FUSE) | Not needed; auto-compaction works |
| VPC connector | Required (~$9/month) | Not needed |
| Compute cost | Min-instance keep-alive | e2-small ~$13/month |
