FROM ubuntu:24.04

RUN apt update -y && \
    apt install -y \
        python3-pip \
        python3-venv \
        git \
        cron

ARG HTTP_PORT
ARG GIT_REPO
ARG GIT_BRANCH

RUN git clone --branch $GIT_BRANCH $GIT_REPO /opt/grouch

WORKDIR /opt/grouch

COPY generated/config.toml config.toml
COPY generated/cron.tab cron.tab
COPY boot.sh boot.sh

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install -r requirements.txt
RUN pip install gunicorn eventlet
RUN chmod a+x boot.sh
RUN crontab cron.tab

ENV FLASK_APP=web/serve.py
ENV PRODUCTION=true
ENV HTTP_PORT=$HTTP_PORT

EXPOSE $HTTP_PORT

ENTRYPOINT ["./boot.sh"]
