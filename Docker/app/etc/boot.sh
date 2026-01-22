#!/bin/bash

# Start cron service for periodic refreshes
service cron start

# Start HTTPS server in the background
gunicorn \
    -b :${HTTPS_PORT} \
    --access-logfile - \
    --error-logfile - \
    --worker-class eventlet \
    --certfile $CERT_PATH/cert.pem \
    --keyfile $CERT_PATH/key.pem \
    -w 1 \
    web.serve:app &

# Start HTTP server in the foreground
exec gunicorn \
    -b :${HTTP_PORT} \
    --access-logfile - \
    --error-logfile - \
    --worker-class eventlet \
    -w 1 \
    web.serve:app
