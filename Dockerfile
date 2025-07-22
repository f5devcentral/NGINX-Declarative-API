FROM alpine:latest

RUN apk update && apk upgrade && \
    apk add --update --no-cache python3 

WORKDIR /deployment

COPY etc/ etc/
COPY src/ src/
COPY templates/ templates/

RUN python3 -m venv /deployment/env/ && \
    source /deployment/env/bin/activate && \
    pip3 install --no-cache --upgrade pip setuptools virtualenv && \
    pip3 install -r src/requirements.txt

WORKDIR /deployment/src
CMD ["/deployment/env/bin/python3", "./main.py"]
