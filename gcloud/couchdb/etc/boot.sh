#!/bin/bash

# Clean up any stale compaction files left by interrupted compactions
find /opt/couchdb/data -name "*.compact.data" -o -name "*.compact" -delete 2>/dev/null || true

if [ -f ./init_db.sh ]; then
    ./init_db.sh &
fi
exec /opt/couchdb/bin/couchdb
