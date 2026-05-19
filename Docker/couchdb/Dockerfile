FROM couchdb:3.5.1

RUN apt update -y && \
    apt install -y jq

COPY etc/local.ini /opt/couchdb/etc/
COPY etc/boot.sh /boot.sh
COPY generated/init_db.sh /init_db.sh

RUN chmod a+x /boot.sh /init_db.sh

EXPOSE $COUCHDB_PORT

CMD ["/boot.sh"]
