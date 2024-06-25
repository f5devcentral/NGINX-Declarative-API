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
-c [start|stop|restart|build]\t- Deployment command\n\n
=== Examples:\n\n
Deploy NGINX DAPI  :\t$0 -c start\n
Remove NGINX DAPI  :\t$0 -c stop\n
Restart NGINX DAPI :\t$0 -c restart\n
Build docker images:\t$0 -c build\n
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

echo "-> Updating docker images"
docker-compose -f $DOCKER_COMPOSE_YAML pull

echo "-> Deploying NGINX Declarative API"
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
# NGINX Declarative API removal
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
# NGINX Declarative API restart
#
nginx_dapi_restart() {
nginx_dapi_stop
nginx_dapi_start
}

#
# Main
#

DOCKER_COMPOSE_YAML="docker-compose.yaml"
PROJECT_NAME="nginx-dapi"

while getopts 'hc:' OPTION
do
        case "$OPTION" in
                h)
			usage
                ;;
                c)
                        ACTION=$OPTARG
                ;;
        esac
done

if [ -z "${ACTION}" ] || [[ ! "${ACTION}" == +(start|stop|restart|build) ]] 
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
    restart)
        nginx_dapi_restart
        ;;
    build)
        nginx_dapi_build
        ;;
esac
