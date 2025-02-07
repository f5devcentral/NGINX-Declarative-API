# Docker compose

NGINX Declarative API can be deployed using docker compose on a Linux virtual machine.

Software prerequisites are:

- [docker-compose v2.20+](https://github.com/docker/compose)
- [jq](https://github.com/jqlang/jq)

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

 -h                     - This help
 -w                     - Enable NGINX App Protect WAF compiler
 -c [start|stop|build]  - Deployment command
 -C [file.crt]          - Certificate to pull packages from the official NGINX repository (mandatory with -w)
 -K [file.key]          - Key to pull packages from the official NGINX repository (mandatory with -w)

 === Examples:

 Deploy NGINX Declarative API:
        no NGINX App Protect compiler:          ./nginx-dapi.sh -c start
        with NGINX App Protect compiler:        ./nginx-dapi.sh -c start -w

 Remove NGINX Declarative API:
        ./nginx-dapi.sh -c stop

 Build docker images:
        no NGINX App Protect compiler:          ./nginx-dapi.sh -c build
        with NGINX App Protect compiler:        ./nginx-dapi.sh -c build -w -C /etc/ssl/nginx/nginx-repo.crt -K /etc/ssl/nginx/nginx-repo.key 

```

## Building docker images

Without NGINX App Protect compiler

```
$ ./nginx-dapi.sh -c build
-> Building NGINX Declarative API Docker images
[+] Building 3.6s (24/24) FINISHED
[...]
 => => exporting layers
[...]

$ docker images
REPOSITORY                        TAG       IMAGE ID       CREATED          SIZE
nginx-declarative-api-devportal   latest    e1bd3cf9965a   1 minutes ago    669MB
nginx-declarative-api             latest    0d76c5a4338b   1 minutes ago    168MB
```

With NGINX App Protect compiler

```
$ ./nginx-dapi.sh -c build -w -C /etc/ssl/nginx/nginx-repo.crt -K /etc/ssl/nginx/nginx-repo.key
-> Building NGINX Declarative API Docker images
-> Including NGINX App Protect WAF compiler tag 5.2.0
[+] Building 118.6s (36/36) FINISHED
[...]
 => => exporting layers
[...]

$ docker images
REPOSITORY                           TAG       IMAGE ID       CREATED              SIZE
nginx-declarative-api-nap-compiler   latest    cbdaa70bba4b   33 seconds ago       691MB
nginx-declarative-api-devportal      latest    ad136e8dc5fd   About a minute ago   669MB
nginx-declarative-api                latest    4c9f89903b6d   About a minute ago   174MB
```

## How to run

1. Start NGINX Declarative API using the provided `nginx-dapi.sh` script
2. Start Postman using the collection provided [here](/contrib/postman)

### Without NGINX App Protect compiler

Starting:

```commandline
$ ./nginx-dapi.sh -c start
-> Deploying NGINX Declarative API
[+] Building 0.0s (0/0)
[+] Running 4/4
 ✔ Network nginx-dapi_dapi-network  Created 
 ✔ Container redis                  Started 
 ✔ Container devportal              Started 
 ✔ Container nginx-dapi             Started 
```

Stopping:

```commandline
$ ./nginx-dapi.sh -c stop
-> Undeploying NGINX Declarative API
[+] Running 4/4
 ✔ Container nginx-dapi             Removed 
 ✔ Container devportal              Removed 
 ✔ Container redis                  Removed 
 ✔ Network nginx-dapi_dapi-network  Removed 
```


#### With NGINX App Protect compiler:

Starting:

```commandline
$ ./nginx-dapi.sh -c start -w
-> Deploying NGINX Declarative API
[+] Building 0.0s (0/0)
[+] Running 5/5
 ✔ Network nginx-dapi_dapi-network  Created 
 ✔ Container redis                  Started 
 ✔ Container nap-compiler           Started 
 ✔ Container devportal              Started 
 ✔ Container nginx-dapi             Started 
```

Stopping:

```commandline
$ ./nginx-dapi.sh -c stop -w
-> Undeploying NGINX Declarative API
[+] Running 5/5
 ✔ Container nginx-dapi             Removed 
 ✔ Container devportal              Removed 
 ✔ Container nap-compiler           Removed 
 ✔ Container redis                  Removed 
 ✔ Network nginx-dapi_dapi-network  Removed
 ```
