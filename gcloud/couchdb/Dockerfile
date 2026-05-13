FROM couchdb:3.5.1

RUN apt update -y && \
    apt install -y jq

COPY generated/creds.sh /creds.sh
COPY generated/local.ini /opt/couchdb/etc/
COPY etc/boot.sh /boot.sh
COPY etc/init_db.sh /init_db.sh

ARG COUCHDB_PORT=5984
ENV COUCHDB_PORT=$COUCHDB_PORT

RUN chmod a+x /boot.sh /init_db.sh

EXPOSE $COUCHDB_PORT

CMD ["/boot.sh"]
