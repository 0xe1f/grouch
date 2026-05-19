FROM nginx:stable

RUN apt-get update && apt-get install -y --no-install-recommends certbot \
    && rm -rf /var/lib/apt/lists/*

RUN rm /etc/nginx/conf.d/default.conf && mkdir -p /var/www/certbot

COPY etc/boot.sh          /usr/local/bin/boot.sh
COPY etc/certbot-renew.sh /usr/local/bin/certbot-renew.sh
RUN chmod +x /usr/local/bin/boot.sh /usr/local/bin/certbot-renew.sh

COPY generated/nginx.conf /etc/nginx/conf.d/grouch.conf
COPY generated/cert.pem   /etc/nginx/cert.pem
COPY generated/key.pem    /etc/nginx/key.pem

CMD ["/usr/local/bin/boot.sh"]
