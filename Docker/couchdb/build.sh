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

# Create init_db.sh script to initialize system databases
echo "#!/bin/bash" > generated/init_db.sh

echo "# Encode username/password" >> generated/init_db.sh
echo "USER_ENCODED=\$(printf %s \"$ADMIN_USER\" | jq -sRr @uri)" >> generated/init_db.sh
echo "PASSWORD_ENCODED=\$(printf %s \"$ADMIN_PASSWORD\" | jq -sRr @uri)" >> generated/init_db.sh
echo "# Wait for CouchDB to become available" >> generated/init_db.sh
echo "for i in {1..10}; do" >> generated/init_db.sh
echo "    if [ \"\$(curl -s -w \"%{http_code}\" http://127.0.0.1:$COUCHDB_PORT/_users)\" != \"000\" ]; then" >> generated/init_db.sh
echo "        break" >> generated/init_db.sh
echo "    fi" >> generated/init_db.sh
echo "    sleep 1" >> generated/init_db.sh
echo "done" >> generated/init_db.sh

echo "# Create system databases if they do not exist" >> generated/init_db.sh
echo "if [ \$(curl -s -o /dev/null -w \"%{http_code}\" http://127.0.0.1:$COUCHDB_PORT/_users) -eq 404 ]; then" >> generated/init_db.sh
echo "    curl -X PUT http://\$USER_ENCODED:\$PASSWORD_ENCODED@127.0.0.1:$COUCHDB_PORT/_users > /dev/null 2>&1" >> generated/init_db.sh
echo "fi" >> generated/init_db.sh
echo "if [ \$(curl -s -o /dev/null -w \"%{http_code}\" http://127.0.0.1:$COUCHDB_PORT/_replicator) -eq 404 ]; then" >> generated/init_db.sh
echo "    curl -X PUT http://\$USER_ENCODED:\$PASSWORD_ENCODED@127.0.0.1:$COUCHDB_PORT/_replicator > /dev/null 2>&1" >> generated/init_db.sh
echo "fi" >> generated/init_db.sh
echo "if [ \$(curl -s -o /dev/null -w \"%{http_code}\" http://127.0.0.1:$COUCHDB_PORT/_global_changes) -eq 404 ]; then" >> generated/init_db.sh
echo "    curl -X PUT http://\$USER_ENCODED:\$PASSWORD_ENCODED@127.0.0.1:$COUCHDB_PORT/_global_changes > /dev/null 2>&1" >> generated/init_db.sh
echo "fi" >> generated/init_db.sh

echo "# Clean up after self" >> generated/init_db.sh
echo "rm -- \"\$0\"" >> generated/init_db.sh

# Execute docker build
docker build \
    --build-arg COUCHDB_PORT=$COUCHDB_PORT \
    -t $IMAGE .
