FROM nginx:stable

RUN rm /etc/nginx/conf.d/default.conf

COPY generated/nginx.conf /etc/nginx/conf.d/grouch.conf
COPY generated/cert.pem   /etc/nginx/cert.pem
COPY generated/key.pem    /etc/nginx/key.pem
