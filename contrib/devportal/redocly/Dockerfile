FROM redocly/cli

WORKDIR /deployment

COPY src src/

RUN apk update && \
    apk add --update --no-cache bash python3 && \
    python3 -m venv /deployment/env && \
    /deployment/env/bin/pip install --no-cache-dir --upgrade pip setuptools && \
    /deployment/env/bin/pip install --no-cache-dir -r /deployment/src/requirements.txt

ENTRYPOINT [ "/deployment/src/start.sh" ]
