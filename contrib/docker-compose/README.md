# Docker compose

NGINX Declarative API can be deployed using docker compose on a Linux virtual machine running Docker.

Usage:

```
$ git clone https://github.com/fabriziofiorucci/NGINX-Declarative-API
$ cd NGINX-Declarative-API/contrib/docker-compose
$ ./nginx-dapi.sh 
NGINX Declarative API - https://github.com/fabriziofiorucci/NGINX-Declarative-API/

 This script is used to deploy/undeploy NGINX Declarative API using docker-compose

 === Usage:

 ./nginx-dapi.sh [options]

 === Options:

 -h                     - This help
 -c [start|stop]        - Deployment command

 === Examples:

 Deploy NGINX DAPI:       ./nginx-dapi.sh -c start
 Remove NGINX DAPI:       ./nginx-dapi.sh -c stop
```

## How to deploy

1. Start NGINX Declarative API using the provided `nginx-dapi.sh` script
2. Start Postman using the collection provided [here](/contrib/postman) or refer to the for CI/CD integration
   - [API v1](/USAGE-v1.md) - deprecated
   - [API v2](/USAGE-v2.md)

## Starting & stopping with docker-compose

Starting NGINX Declarative API:

```
$ ./nginx-dapi.sh -c start
-> Deploying NGINX Declarative API
Creating network "nginx-dapi_default" with the default driver
Creating redis ... done
Creating nginx-dapi ... done
$
```

Stopping NGINX Declarative API:

```
$ ./nginx-dapi.sh -c stop
-> Undeploying NGINX Declarative API
Removing redis ... done
Removing nginx-dapi ... done
Removing network nginx-dapi_default
$
```
