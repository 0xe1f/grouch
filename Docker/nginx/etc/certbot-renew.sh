#!/bin/bash
set -e
[ -n "$DOMAIN" ] || { echo "DOMAIN not set" >&2; exit 0; }

certbot renew --non-interactive
cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" /etc/nginx/cert.pem
cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem"   /etc/nginx/key.pem

# Prefer nginx's reload signal; fall back to HUP on the master (often PID 1
# under `daemon off;`) when the pid file is missing inside the container.
if ! nginx -s reload 2>/dev/null; then
    echo "nginx -s reload failed; sending HUP to master process" >&2
    kill -HUP 1
fi
