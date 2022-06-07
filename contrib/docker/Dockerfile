FROM alpine:latest

RUN apk update && apk upgrade && \
    apk add --update --no-cache python3 redis && \
    python3 -m ensurepip

WORKDIR /deployment

COPY etc/ etc/
COPY src/ src/
COPY templates/ templates/
COPY contrib/docker/start.sh /deployment/src/

RUN chmod +x /deployment/src/start.sh && \
    pip3 install --no-cache --upgrade pip setuptools virtualenv && \
    virtualenv /deployment/env/ && source /deployment/env/bin/activate && \
    python -m pip install --upgrade pip && \
    pip3 install -r src/requirements.txt

WORKDIR /deployment/src
CMD ["./start.sh"]
