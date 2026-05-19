#!/bin/bash
set -e
[ -n "$DOMAIN" ] || { echo "DOMAIN not set" >&2; exit 0; }

certbot renew --non-interactive
cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" /etc/nginx/cert.pem
cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem"   /etc/nginx/key.pem
nginx -s reload
