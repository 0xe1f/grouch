FROM couchdb

RUN apt update -y && \
    apt install -y jq

COPY generated/init_db.sh init_db.sh
COPY generated/local.ini /opt/couchdb/etc/
ARG COUCHDB_PORT

ENV COUCHDB_PORT=$COUCHDB_PORT

RUN chmod a+x init_db.sh

EXPOSE $COUCHDB_PORT
