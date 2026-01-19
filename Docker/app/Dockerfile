FROM python:3.12-slim

RUN apt update -y && \
    apt install -y \
        git \
        cron \
        tini

ARG HTTP_PORT
ARG GIT_REPO
ARG GIT_BRANCH

RUN git clone --branch $GIT_BRANCH $GIT_REPO /opt/grouch

COPY etc/cron.tab /cron.tab
COPY etc/boot.sh /boot.sh

WORKDIR /opt/grouch
COPY generated/config.toml config.toml

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install -r requirements.txt
RUN pip install gunicorn eventlet
RUN chmod a+x /boot.sh
RUN crontab /cron.tab

ENV FLASK_APP=web/serve.py
ENV PRODUCTION=true
ENV HTTP_PORT=$HTTP_PORT

EXPOSE $HTTP_PORT

ENTRYPOINT ["tini", "--", "/boot.sh"]
