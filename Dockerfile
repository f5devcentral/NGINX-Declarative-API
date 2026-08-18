FROM alpine:latest

RUN apk update && apk upgrade && \
    apk add --update --no-cache python3 

WORKDIR /deployment

COPY etc/ etc/
COPY src/ src/
COPY templates/ templates/

RUN python3 -m venv /deployment/env && \
    /deployment/env/bin/pip install --no-cache-dir --upgrade pip setuptools virtualenv && \
    /deployment/env/bin/pip install --no-cache-dir -r src/requirements.txt

WORKDIR /deployment/src
CMD ["/deployment/env/bin/python3", "./main.py"]
