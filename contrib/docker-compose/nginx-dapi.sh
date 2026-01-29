#!/bin/bash

#
# Usage
#
usage() {
BANNER="NGINX Declarative API - https://github.com/f5devcentral/NGINX-Declarative-API/\n\n
This script is used to deploy/undeploy NGINX Declarative API using docker-compose\n\n
=== Usage:\n\n
$0 [options]\n\n
=== Options:\n\n
-h\t\t\t\t- This help\n
-c [start|stop|build]\t\t- Deployment command\n
-a <port>\t\t\t- Custom port for NGINX Declarative API (default: 5000)\n
-d <port>\t\t\t- Custom port for Developer Portal (default: 5001)\n
-r <port>\t\t\t- Custom port for Redis (default: 6379)\n\n
=== Examples:\n\n
Deploy NGINX Declarative API:\t\t\t$0 -c start\n
Deploy with custom Declarative API port:\t$0 -c start -a 8080\n
Deploy with custom DevPortal port:\t\t$0 -c start -d 8081\n
Deploy with all custom ports:\t\t\t$0 -c start -a 8080 -d 8081 -r 6380\n
Remove NGINX Declarative API:\t\t\t$0 -c stop\n
Build docker images:\t\t\t\t$0 -c build\n
"

echo -e $BANNER 2>&1
exit 1
}

#
# NGINX Declarative API deployment
#
nginx_dapi_start() {

# Docker compose variables
USERNAME=`whoami`
export USERID=`id -u $USERNAME`
export USERGROUP=`id -g $USERNAME`
export DAPI_PORT=${DAPI_PORT:-5000}
export DEVPORTAL_PORT=${DEVPORTAL_PORT:-5001}
export REDIS_PORT=${REDIS_PORT:-6379}

echo "-> Deploying NGINX Declarative API"
echo "   NGINX Declarative API port: $DAPI_PORT"
echo "   Developer Portal port: $DEVPORTAL_PORT"
echo "   Redis port: $REDIS_PORT"
COMPOSE_HTTP_TIMEOUT=240 docker-compose -p $PROJECT_NAME -f $DOCKER_COMPOSE_YAML up -d --remove-orphans
}

#
# NGINX Declarative API removal
#
nginx_dapi_stop() {

# Docker compose variables
USERNAME=`whoami`
export USERID=`id -u $USERNAME`
export USERGROUP=`id -g $USERNAME`

echo "-> Undeploying NGINX Declarative API"
COMPOSE_HTTP_TIMEOUT=240 docker-compose -p $PROJECT_NAME -f $DOCKER_COMPOSE_YAML down
}

#
# NGINX Declarative API image build
#
nginx_dapi_build() {

# Docker compose variables
USERNAME=`whoami`
export USERID=`id -u $USERNAME`
export USERGROUP=`id -g $USERNAME`

echo "-> Building NGINX Declarative API Docker images"

COMPOSE_HTTP_TIMEOUT=240 docker-compose -p $PROJECT_NAME -f $DOCKER_COMPOSE_YAML build
}

#
# Main
#

DOCKER_COMPOSE_YAML="docker-compose.yaml"
PROJECT_NAME="nginx-dapi"

while getopts 'hc:a:d:r:' OPTION
do
  case "$OPTION" in
    h)
      usage
    ;;
    c)
      ACTION=$OPTARG
    ;;
    a)
      DAPI_PORT=$OPTARG
    ;;
    d)
      DEVPORTAL_PORT=$OPTARG
    ;;
    r)
      REDIS_PORT=$OPTARG
    ;;
  esac
done

if [ -z "${ACTION}" ] || [[ ! "${ACTION}" =~ ^(start|stop|build)$ ]]
then
  usage
fi

case "$ACTION" in
  start)
    nginx_dapi_start
  ;;
  stop)
    nginx_dapi_stop
  ;;
  build)
    nginx_dapi_build
  ;;
esac
