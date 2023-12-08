FROM redocly/cli

WORKDIR /deployment

COPY src/ src/

RUN apk update && \
    apk add --update --no-cache bash python3 && \
    python3 -m ensurepip && \
    pip3 install --no-cache --upgrade pip setuptools virtualenv && \
    virtualenv /deployment/env/ && source /deployment/env/bin/activate && \
    python3 -m pip install --upgrade pip && \
    pip3 install -r /deployment/src/requirements.txt

ENTRYPOINT [ "/deployment/src/start.sh" ]
