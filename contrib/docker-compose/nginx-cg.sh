#!/bin/bash

#
# Usage
#
usage() {
BANNER="NGINX Config Generator - https://github.com/fabriziofiorucci/NGINX-Config-Generator/\n\n
This script is used to deploy/undeploy NGINX Config Generator using docker-compose\n\n
=== Usage:\n\n
$0 [options]\n\n
=== Options:\n\n
-h\t\t\t- This help\n
-c [start|stop]\t- Deployment command\n\n
=== Examples:\n\n
Deploy NGINX CG:\t$0 -c start\n
Remove NGINX CG:\t$0 -c stop\n
"

echo -e $BANNER 2>&1
exit 1
}

#
# NGINX Config Generator deployment
#
nginx_cg_start() {

# Docker compose variables
USERNAME=`whoami`
export USERID=`id -u $USERNAME`
export USERGROUP=`id -g $USERNAME`

echo "-> Deploying NGINX Config Generator"
COMPOSE_HTTP_TIMEOUT=240 docker-compose -p $PROJECT_NAME -f $DOCKER_COMPOSE_YAML up -d --remove-orphans
}

#
# NGINX Config Generator removal
#
nginx_cg_stop() {

# Docker compose variables
USERNAME=`whoami`
export USERID=`id -u $USERNAME`
export USERGROUP=`id -g $USERNAME`

echo "-> Undeploying NGINX Config Generator"
COMPOSE_HTTP_TIMEOUT=240 docker-compose -p $PROJECT_NAME -f $DOCKER_COMPOSE_YAML down
}

#
# Main
#

DOCKER_COMPOSE_YAML=docker-compose.yaml
PROJECT_NAME=nginx-cg

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

nginx_cg_$ACTION
