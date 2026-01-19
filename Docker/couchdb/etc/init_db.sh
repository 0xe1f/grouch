#!/bin/bash

. creds.sh

MAX_RETRIES=10
RETRY_INTERVAL_SEC=1

# Encode username/password
USER_ENCODED=$(printf %s "$COUCHDB_ADMIN_USER" | jq -sRr @uri)
PASSWORD_ENCODED=$(printf %s "$COUCHDB_ADMIN_PASSWORD" | jq -sRr @uri)

echo "Connecting..." >&2

# Wait for CouchDB to become available
for I in $(seq 1 $MAX_RETRIES); do
    if [ "$(curl -s -w "%{http_code}" http://$COUCHDB_HOST:$COUCHDB_PORT/_users)" != "000" ]; then
        break
    fi
    if [ $I -eq $MAX_RETRIES ]; then
        echo "CouchDB unreachable within the timeout." >&2
        exit 1
    fi
    sleep $RETRY_INTERVAL_SEC
done

echo "Connected." >&2

# Create system databases if they do not exist
if [ $(curl -s -o /dev/null -w "%{http_code}" http://$COUCHDB_HOST:$COUCHDB_PORT/_users) -eq 404 ]; then
    echo "Creating _users database..." >&2
    curl -X PUT http://$USER_ENCODED:$PASSWORD_ENCODED@$COUCHDB_HOST:$COUCHDB_PORT/_users > /dev/null 2>&1
fi
if [ $(curl -s -o /dev/null -w "%{http_code}" http://$COUCHDB_HOST:$COUCHDB_PORT/_replicator) -eq 404 ]; then
    echo "Creating _replicator database..." >&2
    curl -X PUT http://$USER_ENCODED:$PASSWORD_ENCODED@$COUCHDB_HOST:$COUCHDB_PORT/_replicator > /dev/null 2>&1
fi
if [ $(curl -s -o /dev/null -w "%{http_code}" http://$USER_ENCODED:$PASSWORD_ENCODED@$COUCHDB_HOST:$COUCHDB_PORT/_global_changes) -eq 404 ]; then
    echo "Creating _global_changes database..." >&2
    curl -X PUT http://$USER_ENCODED:$PASSWORD_ENCODED@$COUCHDB_HOST:$COUCHDB_PORT/_global_changes > /dev/null 2>&1
fi

echo "Cleaning up..." >&2

# Clean up
rm -f creds.sh
rm -f -- "$0"

echo "CouchDB initialization complete." >&2
