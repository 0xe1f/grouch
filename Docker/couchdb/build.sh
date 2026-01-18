#!/bin/bash

NETWORK=${NETWORK:-"grouch"}
NAME="couchdb.$NETWORK"
IMAGE="$NETWORK/couchdb"

COUCHDB_PORT=${COUCHDB_PORT:-5984}

# Create temp directory
mkdir -p generated

# Generate random admin username and password
ADMIN_USER=`LC_ALL=C tr -dc 'A-Za-z' </dev/urandom | head -c 8; echo`
ADMIN_PASSWORD=`LC_ALL=C tr -dc 'A-Za-z0-9%_-+;:.' </dev/urandom | head -c 16; echo`

# Update local.ini with generated credentials and port
sed \
    -e "s/^;admin = .*/$ADMIN_USER = $ADMIN_PASSWORD/" \
    -e "s/^;port = .*/port = $COUCHDB_PORT/" \
    local.ini.default > generated/local.ini

# Create set_creds.sh script to set credentials
echo "#!/bin/bash" > generated/set_creds.sh

echo "COUCHDB_HOST=\"$NAME\"" >> generated/set_creds.sh
echo "COUCHDB_PORT=\"$COUCHDB_PORT\"" >> generated/set_creds.sh
echo "COUCHDB_ADMIN_USER=\"$ADMIN_USER\"" >> generated/set_creds.sh
echo "COUCHDB_ADMIN_PASSWORD=\"$ADMIN_PASSWORD\"" >> generated/set_creds.sh

# Execute docker build
docker build \
    --build-arg COUCHDB_PORT=$COUCHDB_PORT \
    -t $IMAGE .
