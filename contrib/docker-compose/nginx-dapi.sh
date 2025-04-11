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
-h\t\t\t- This help\n
-w \t\t\t- Enable NGINX App Protect WAF compiler\n
-c [start|stop|build]\t- Deployment command\n
-C [file.crt]\t\t- Certificate to pull packages from the official NGINX repository (mandatory with -w)\n
-K [file.key]\t\t- Key to pull packages from the official NGINX repository (mandatory with -w)\n\n
=== Examples:\n\n
Deploy NGINX Declarative API:\n
\tno NGINX App Protect compiler:\t\t$0 -c start\n
\twith NGINX App Protect compiler:\t$0 -c start -w\n\n
Remove NGINX Declarative API:\n
\t$0 -c stop\n\n
Build docker images:\n
\tno NGINX App Protect compiler:\t\t$0 -c build\n
\twith NGINX App Protect compiler:\t$0 -c build -w -C /etc/ssl/nginx/nginx-repo.crt -K /etc/ssl/nginx/nginx-repo.key
\n"

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

echo "-> Deploying NGINX Declarative API"
COMPOSE_HTTP_TIMEOUT=240 docker-compose -p $PROJECT_NAME -f $DOCKER_COMPOSE_YAML $DOCKER_COMPOSE_PROFILE up -d --remove-orphans
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
#COMPOSE_HTTP_TIMEOUT=240 docker-compose -p $PROJECT_NAME -f $DOCKER_COMPOSE_YAML $DOCKER_COMPOSE_PROFILE down
COMPOSE_HTTP_TIMEOUT=240 docker-compose -p $PROJECT_NAME -f $DOCKER_COMPOSE_YAML --profile nap down
}

#
# NGINX Declarative API removal
#
nginx_dapi_build() {

# Docker compose variables
USERNAME=`whoami`
export USERID=`id -u $USERNAME`
export USERGROUP=`id -g $USERNAME`

echo "-> Building NGINX Declarative API Docker images"
if ([ ! "${NGINX_CERT}" = "unused" ] && [ ! "${NGINX_KEY}" = "unused" ])
then
  export NAP_COMPILER_TAG=`curl -s https://private-registry.nginx.com/v2/nap/waf-compiler/tags/list --key $NGINX_KEY --cert $NGINX_CERT | jq -r '.tags|max'`
  echo "-> Including NGINX App Protect WAF compiler tag $NAP_COMPILER_TAG"
fi

COMPOSE_HTTP_TIMEOUT=240 docker-compose -p $PROJECT_NAME -f $DOCKER_COMPOSE_YAML $DOCKER_COMPOSE_PROFILE build
}

#
# Main
#

DOCKER_COMPOSE_YAML="docker-compose.yaml"
PROJECT_NAME="nginx-dapi"
export NGINX_CERT="unused"
export NGINX_KEY="unused"
export PROFILE="basic"
export NAP_COMPILER_TAG="unused"
export DOCKER_COMPOSE_PROFILE=""

while getopts 'hc:C:K:w' OPTION
do
  case "$OPTION" in
    h)
      usage
    ;;
    c)
      ACTION=$OPTARG
    ;;
    w)
      NAP_ENABLED=true
      export DOCKER_COMPOSE_PROFILE="--profile nap"
    ;;
    C)
      export NGINX_CERT=$OPTARG
    ;;
    K)
      export NGINX_KEY=$OPTARG
    ;;
  esac
done

if [ -z "${ACTION}" ] || [[ ! "${ACTION}" == +(start|stop|build) ]]
then
  usage
fi

if [ "${ACTION}" == "build" ] && [ "${NAP_ENABLED}" == "true" ]
then
  if [ "${NGINX_CERT}" == "unused" ] || [ "${NGINX_KEY}" == "unused" ]
  then
    echo "NGINX certificate and key missing"
    exit
  fi
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
