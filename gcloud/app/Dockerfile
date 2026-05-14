FROM python:3.12-slim

RUN apt update -y && \
    apt install -y \
        git \
        tini

ARG HTTP_PORT=8080
ARG GIT_REPO
ARG GIT_BRANCH
ARG ETC_PATH=/etc/grouch

RUN git clone --branch $GIT_BRANCH $GIT_REPO /opt/grouch

COPY etc/boot.sh $ETC_PATH/boot.sh

WORKDIR /opt/grouch
COPY generated/config.toml config.toml

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install -r requirements.txt
RUN pip install gunicorn "gevent==26.4.0"
RUN chmod a+x $ETC_PATH/boot.sh

ENV FLASK_APP=web/serve.py
ENV PRODUCTION=true
ENV HTTP_PORT=$HTTP_PORT

EXPOSE $HTTP_PORT

ENTRYPOINT [ "tini", "--", "/etc/grouch/boot.sh" ]
