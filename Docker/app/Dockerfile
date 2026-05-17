FROM python:3.12-slim

RUN apt update -y && \
    apt install -y \
        cron \
        tini

ARG HTTP_PORT
ARG GIT_HASH=dev
ARG BUILD_DATE=dev
ARG ETC_PATH=/etc/grouch

COPY . /opt/grouch

RUN sed -i \
    -e "s/^HASH       = .*/HASH       = \"$GIT_HASH\"/" \
    -e "s/^BUILD_DATE = .*/BUILD_DATE = \"$BUILD_DATE\"/" \
    /opt/grouch/version.py

COPY Docker/app/etc/cron.tab $ETC_PATH/cron.tab
COPY Docker/app/etc/boot.sh $ETC_PATH/boot.sh

WORKDIR /opt/grouch
COPY Docker/app/generated/config.toml config.toml

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install -r requirements.txt
RUN pip install gunicorn "gevent==26.4.0"
RUN chmod a+x $ETC_PATH/boot.sh
RUN crontab $ETC_PATH/cron.tab

ENV FLASK_APP=web/serve.py
ENV PRODUCTION=true
ENV HTTP_PORT=$HTTP_PORT

EXPOSE $HTTP_PORT

ENTRYPOINT [ "tini", "--", "/etc/grouch/boot.sh" ]
