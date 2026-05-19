#!/bin/bash
set -e

if [ "$CERT_SOURCE" != "custom" ] && [ -n "$DOMAIN" ]; then
    if [ -n "$LETSENCRYPT_EMAIL" ]; then
        EMAIL_ARGS="--email $LETSENCRYPT_EMAIL --no-eff-email"
    else
        EMAIL_ARGS="--register-unsafely-without-email"
    fi

    # Start nginx temporarily to serve the ACME webroot challenge
    nginx
    sleep 1

    if certbot certonly --webroot \
        -w /var/www/certbot \
        -d "$DOMAIN" \
        $EMAIL_ARGS \
        --agree-tos \
        --non-interactive \
        --keep-until-expiring; then
        cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" /etc/nginx/cert.pem
        cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem"   /etc/nginx/key.pem
        echo "Let's Encrypt certificate installed for $DOMAIN."
    else
        echo "WARNING: certbot failed for $DOMAIN — using baked-in certificate." >&2
        echo "Ensure DNS is pointed to this host and port 80 is reachable, then restart nginx." >&2
    fi

    nginx -s quit
    sleep 1
fi

exec nginx -g "daemon off;"
