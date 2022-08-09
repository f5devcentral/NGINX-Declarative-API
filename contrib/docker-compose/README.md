# Docker compose

NGINX Config Generator can be deployed using docker compose on a Linux virtual machine running Docker.

The current version of the `docker-compose.yaml` file uses no persistent storage for redis.

Usage:

```
$ git clone https://github.com/fabriziofiorucci/NGINX-Config-Generator
$ cd NGINX-Config-Generator/contrib/docker-compose
$ ./nginx-cg.sh 
NGINX Config Generator - https://github.com/fabriziofiorucci/NGINX-Config-Generator/

 This script is used to deploy/undeploy NGINX Config Generator using docker-compose

 === Usage:

 ./nginx-cg.sh [options]

 === Options:

 -h                     - This help
 -c [start|stop]        - Deployment command

 === Examples:

 Deploy NGINX CG:       ./nginx-cg.sh -c start
 Remove NGINX CG:       ./nginx-cg.sh -c stop
```

## How to deploy

1. Start NGINX Config Generator using the provided `nginx-cg.sh` script
2. Start Postman using the collection provided [here](https://github.com/fabriziofiorucci/NGINX-Config-Generator/tree/main/contrib/postman) or refer to the [usage page](https://github.com/fabriziofiorucci/NGINX-Config-Generator/blob/main/USAGE.md) for CI/CD integration

## Starting & stopping with docker-compose

Starting NGINX Config Generator:

```
$ ./nginx-cg.sh -c start
-> Deploying NGINX Config Generator
Creating network "nginx-cg_default" with the default driver
Creating redis ... done
Creating nginx-cg ... done
$
```

Stopping NGINX Config Generator:

```
$ ./nginx-cg.sh -c stop
-> Undeploying NGINX Config Generator
Removing redis ... done
Removing nginx-cg ... done
Removing network nginx-cg_default
$
```