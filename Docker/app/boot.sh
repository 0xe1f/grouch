#!/bin/bash

exec gunicorn \
    -b :${HTTP_PORT} \
    --access-logfile - \
    --error-logfile - \
    --worker-class eventlet \
    -w 1 \
    web.serve:app
