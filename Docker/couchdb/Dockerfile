FROM couchdb:3.5.1

RUN apt update -y && \
    apt install -y jq

COPY generated/set_creds.sh set_creds.sh
COPY generated/local.ini /opt/couchdb/etc/
COPY init_db.sh init_db.sh
ARG COUCHDB_PORT

ENV COUCHDB_PORT=$COUCHDB_PORT

RUN chmod a+x init_db.sh

EXPOSE $COUCHDB_PORT
