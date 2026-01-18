#!/bin/bash

set -e
. set_creds.sh

# Encode username/password
USER_ENCODED=$(printf %s "$COUCHDB_ADMIN_USER" | jq -sRr @uri)
PASSWORD_ENCODED=$(printf %s "$COUCHDB_ADMIN_PASSWORD" | jq -sRr @uri)

# Wait for CouchDB to become available
CONNECTED=0
for i in {1..10}; do
    if [ "$(curl -s -w "%{http_code}" http://$COUCHDB_HOST:$COUCHDB_PORT/_users)" != "000" ]; then
        CONNECTED=1
        break
    fi
    sleep 0.5
done

# Check exit status
if [ $CONNECTED -eq 0 ]; then
    echo "CouchDB unreachable within the timeout."
    exit 1
fi

# Create system databases if they do not exist
if [ $(curl -s -o /dev/null -w "%{http_code}" http://$COUCHDB_HOST:$COUCHDB_PORT/_users) -eq 404 ]; then
    curl -X PUT http://$USER_ENCODED:$PASSWORD_ENCODED@$COUCHDB_HOST:$COUCHDB_PORT/_users > /dev/null 2>&1
fi
if [ $(curl -s -o /dev/null -w "%{http_code}" http://$COUCHDB_HOST:$COUCHDB_PORT/_replicator) -eq 404 ]; then
    curl -X PUT http://$USER_ENCODED:$PASSWORD_ENCODED@$COUCHDB_HOST:$COUCHDB_PORT/_replicator > /dev/null 2>&1
fi
if [ $(curl -s -o /dev/null -w "%{http_code}" http://$COUCHDB_HOST:$COUCHDB_PORT/_global_changes) -eq 404 ]; then
    curl -X PUT http://$USER_ENCODED:$PASSWORD_ENCODED@$COUCHDB_HOST:$COUCHDB_PORT/_global_changes > /dev/null 2>&1
fi

# Clean up
rm -f set_creds.sh
rm -f -- "$0"
