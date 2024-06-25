# Docker compose

NGINX Declarative API can be deployed using docker compose on a Linux virtual machine running docker-compose v2.20+

Usage:

```
$ git clone https://github.com/f5devcentral/NGINX-Declarative-API
$ cd NGINX-Declarative-API/contrib/docker-compose
$ ./nginx-dapi.sh 
NGINX Declarative API - https://github.com/f5devcentral/NGINX-Declarative-API/

 This script is used to deploy/undeploy NGINX Declarative API using docker-compose

 === Usage:

 ./nginx-dapi.sh [options]

 === Options:

 -h                             - This help
 -c [start|stop|restart|build]  - Deployment command

 === Examples:

 Deploy NGINX DAPI :    ./nginx-dapi.sh -c start
 Remove NGINX DAPI :    ./nginx-dapi.sh -c stop
 Restart NGINX DAPI :   ./nginx-dapi.sh -c restart
 Build docker images:   ./nginx-dapi.sh -c build
```

## How to deploy

1. Start NGINX Declarative API using the provided `nginx-dapi.sh` script
2. Start Postman using the collection provided [here](/contrib/postman)

## How to run

Starting NGINX Declarative API:

```
$ ./nginx-dapi.sh -c start
-> Updating docker images
[+] Pulling 3/3
 ✔ nginx-dapi Pulled 
 ✔ redis Pulled 
 ✔ devportal Pulled 
-> Deploying NGINX Declarative API
[+] Running 3/3
 ✔ Container redis       Running 
 ✔ Container devportal   Running 
 ✔ Container nginx-dapi  Started
```

Stopping NGINX Declarative API:

```
$ ./nginx-dapi.sh -c stop
-> Undeploying NGINX Declarative API
[+] Running 4/4
 ✔ Container nginx-dapi        Removed 
 ✔ Container devportal         Removed 
 ✔ Container redis             Removed 
 ✔ Network nginx-dapi_default  Removed 
```

Restarting NGINX Declarative API:

```
$ ./nginx-dapi.sh -c restart
[+] Running 4/4
 ✔ Container devportal         Removed 
 ✔ Container nginx-dapi        Removed 
 ✔ Container redis             Removed 
 ✔ Network nginx-dapi_default  Removed 
-> Updating docker images
[+] Pulling 3/3
 ✔ nginx-dapi Pulled 
 ✔ redis Pulled 
 ✔ devportal Pulled 
-> Deploying NGINX Declarative API
[+] Running 4/4
 ✔ Network nginx-dapi_default  Created-> Undeploying NGINX Declarative API
[+] Running 4/4
 ✔ Container nginx-dapi        Removed 
 ✔ Container devportal         Removed 
 ✔ Container redis             Removed 
 ✔ Network nginx-dapi_default  Removed
 ✔ Container devportal         Started 
 ✔ Container redis             Started 
 ✔ Container nginx-dapi        Started
```

Building NGINX Declarative API docker images:

```
$ ./nginx-dapi.sh -c build
-> Building NGINX Declarative API Docker images
[+] Building 3.6s (24/24) FINISHED
[...]
 => => exporting layers
 => => writing image sha256:e1bd3cf9965a015161847038a13e4df319bf5a2771ecfd0d1b5e9a9b3d404053
 => => naming to docker.io/library/nginx-declarative-api-devportal

$ docker images
REPOSITORY                        TAG       IMAGE ID       CREATED          SIZE
nginx-declarative-api             latest    0d76c5a4338b   1 minutes ago    168MB
nginx-declarative-api-devportal   latest    e1bd3cf9965a   1 minutes ago    669MB
```
