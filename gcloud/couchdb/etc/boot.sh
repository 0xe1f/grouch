#!/bin/bash

if [ -f ./init_db.sh ]; then
    ./init_db.sh &
fi
exec /opt/couchdb/bin/couchdb
