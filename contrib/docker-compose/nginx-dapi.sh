#!/bin/bash

#
# Usage
#
usage() {
BANNER="NGINX Declarative API - https://github.com/fabriziofiorucci/NGINX-Declarative-API/\n\n
This script is used to deploy/undeploy NGINX Declarative API using docker-compose\n\n
=== Usage:\n\n
$0 [options]\n\n
=== Options:\n\n
-h\t\t\t- This help\n
-c [start|stop]\t- Deployment command\n\n
=== Examples:\n\n
Deploy NGINX DAPI:\t$0 -c start\n
Remove NGINX DAPI:\t$0 -c stop\n
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

if [ -z "${ACTION}" ] || [[ ! "${ACTION}" == +(start|stop) ]] 
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
esac
