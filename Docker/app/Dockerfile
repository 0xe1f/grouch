FROM ubuntu:24.04

RUN apt update -y && \
    apt install -y \
        python3-pip \
        python3-venv \
        python-is-python3 \
        git

ARG HTTP_PORT
ARG GIT_REPO
ARG GIT_BRANCH

RUN git clone --branch $GIT_BRANCH $GIT_REPO /opt/grouch
COPY generated/config.toml /opt/grouch/config.toml
COPY boot.sh /opt/grouch/boot.sh

WORKDIR /opt/grouch
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install -r requirements.txt
RUN pip install gunicorn eventlet
RUN chmod a+x boot.sh

ENV FLASK_APP=web/serve.py
ENV PRODUCTION=true
ENV HTTP_PORT=$HTTP_PORT

EXPOSE $HTTP_PORT

ENTRYPOINT ["./boot.sh"]
