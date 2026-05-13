#!/bin/bash

# Start cron service for periodic refreshes
service cron start

# Start HTTP server (TLS is terminated by Cloud Run)
exec gunicorn \
    -b :${PORT:-8080} \
    --access-logfile - \
    --error-logfile - \
    --worker-class gevent \
    -w 1 \
    web.serve:app
