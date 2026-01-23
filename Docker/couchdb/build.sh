#!/bin/bash

NETWORK=${NETWORK:-"grouch"}
NAME="couchdb.$NETWORK"
IMAGE="$NETWORK/couchdb"

COUCHDB_PORT=${COUCHDB_PORT:-5984}

mkdir -p generated

if [ ! -f generated/creds.sh ]; then
    # Generate random admin username and password
    COUCHDB_ADMIN_USER=`LC_ALL=C tr -dc 'A-Za-z' </dev/urandom | head -c 8; echo`
    COUCHDB_ADMIN_PASSWORD=`LC_ALL=C tr -dc 'A-Za-z0-9%_+;:.-' </dev/urandom | head -c 16; echo`

    # Create creds.sh script to set credentials
    echo "#!/bin/bash" > generated/creds.sh

    echo "COUCHDB_HOST=\"$NAME\"" >> generated/creds.sh
    echo "COUCHDB_PORT=\"$COUCHDB_PORT\"" >> generated/creds.sh
    echo "COUCHDB_ADMIN_USER=\"$COUCHDB_ADMIN_USER\"" >> generated/creds.sh
    echo "COUCHDB_ADMIN_PASSWORD=\"$COUCHDB_ADMIN_PASSWORD\"" >> generated/creds.sh
else
    . generated/creds.sh
fi

# Update local.ini with credentials and port
sed \
    -e "s/^;admin = .*/$COUCHDB_ADMIN_USER = $COUCHDB_ADMIN_PASSWORD/" \
    -e "s/^;port = .*/port = $COUCHDB_PORT/" \
    etc/local.ini.default > generated/local.ini

# Execute docker build
docker build \
    --build-arg COUCHDB_PORT=$COUCHDB_PORT \
    -t $IMAGE . \
    $@
