FROM python:3.12-slim

RUN apt update -y && \
    apt install -y \
        git \
        cron \
        tini

ARG HTTP_PORT
ARG HTTPS_PORT
ARG GIT_REPO
ARG GIT_BRANCH
ARG ETC_PATH=/etc/grouch
ARG CERT_PATH=$ETC_PATH

RUN git clone --branch $GIT_BRANCH $GIT_REPO /opt/grouch

COPY etc/cron.tab $ETC_PATH/cron.tab
COPY etc/boot.sh $ETC_PATH/boot.sh
COPY generated/cert.pem $CERT_PATH/cert.pem
COPY generated/key.pem $CERT_PATH/key.pem

WORKDIR /opt/grouch
COPY generated/config.toml config.toml

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install -r requirements.txt
RUN pip install gunicorn "gevent==26.4.0"
RUN chmod a+x $ETC_PATH/boot.sh
RUN crontab $ETC_PATH/cron.tab

ENV FLASK_APP=web/serve.py
ENV PRODUCTION=true
ENV HTTP_PORT=$HTTP_PORT
ENV HTTPS_PORT=$HTTPS_PORT
ENV CERT_PATH=$CERT_PATH

EXPOSE $HTTP_PORT
EXPOSE $HTTPS_PORT

ENTRYPOINT [ "tini", "--", "/etc/grouch/boot.sh" ]
