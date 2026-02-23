#!/bin/sh
set -e

# Default DAPI port if not provided
DAPI_PORT=${DAPI_PORT:-5000}

# Replace the DAPI_PORT placeholder in nginx config
sed -i "s/DAPI_PORT_PLACEHOLDER/${DAPI_PORT}/g" /etc/nginx/conf.d/default.conf

# Execute the main container command
exec "$@"
