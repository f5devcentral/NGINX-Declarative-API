#!/bin/bash

# https://redocly.com/docs/cli/commands/build-docs/

# Disable telemetry collection
# https://github.com/Redocly/redocly-cli/#data-collection
export REDOCLY_TELEMETRY=off

/deployment/env/bin/python /deployment/src/server.py
