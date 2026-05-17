#!/bin/bash

exec /opt/venv/bin/celery -A tasks.celery_app worker \
    --loglevel=info \
    --concurrency=2
