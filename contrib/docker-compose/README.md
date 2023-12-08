# Docker compose

NGINX Declarative API can be deployed using docker compose on a Linux virtual machine running docker-compose v2.20+

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

 -h                             - This help
 -c [start|stop|restart]        - Deployment command

 === Examples:

 Deploy NGINX DAPI :    ./nginx-dapi.sh -c start
 Remove NGINX DAPI :    ./nginx-dapi.sh -c stop
 Restart NGINX DAPI:    ./nginx-dapi.sh -c restart
```

## How to deploy

1. Start NGINX Declarative API using the provided `nginx-dapi.sh` script
2. Start Postman using the collection provided [here](/contrib/postman) or refer to the for CI/CD integration
   - [API v1](/USAGE-v1.md) - deprecated
   - [API v2](/USAGE-v2.md)

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