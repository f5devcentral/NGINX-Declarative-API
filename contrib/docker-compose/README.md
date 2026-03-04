# Docker compose

NGINX Declarative API can be deployed using docker compose on a Linux virtual machine.

Software prerequisites are:

- [docker-compose v2.20+](https://github.com/docker/compose)
- [jq](https://github.com/jqlang/jq)

Usage:

```bash
$ git clone https://github.com/f5devcentral/NGINX-Declarative-API
$ cd NGINX-Declarative-API/contrib/docker-compose
$ ./nginx-dapi.sh 
NGINX Declarative API - https://github.com/f5devcentral/NGINX-Declarative-API/

 This script is used to deploy/undeploy NGINX Declarative API using docker-compose

 === Usage:

 ./nginx-dapi.sh [options]

 === Options:

 -h                             - This help
 -c [start|stop|build]          - Deployment command
 -m [full|dev]                  - Deployment mode: full (with webui container) or dev (backend only for local webui development) (default: full)
 -a <port>                      - Custom port for NGINX Declarative API (default: 5000)
 -w <port>                      - Custom port for Web UI (default: 3000, only for full mode)
 -d <port>                      - Custom port for Developer Portal (default: 5001)
 -r <port>                      - Custom port for Redis (default: 6379)

 === Examples:

 Deploy NGINX Declarative API (full):           ./nginx-dapi.sh -c start
 Deploy in dev mode (no webui container):       ./nginx-dapi.sh -c start -m dev
 Deploy with custom Declarative API port:       ./nginx-dapi.sh -c start -a 8080
 Deploy dev mode with custom ports:             ./nginx-dapi.sh -c start -m dev -a 8080 -d 8081 -r 6380
 Deploy with custom Web UI port:                ./nginx-dapi.sh -c start -w 8080
 Deploy with custom DevPortal port:             ./nginx-dapi.sh -c start -d 8081
 Deploy with all custom ports:                  ./nginx-dapi.sh -c start -a 8080 -w 8081 -d 8082 -r 6380
 Remove NGINX Declarative API:                  ./nginx-dapi.sh -c stop
 Build docker images:                           ./nginx-dapi.sh -c build
```

## Building docker images

```bash
$ ./nginx-dapi.sh -c build
-> Building NGINX Declarative API Docker images
[+] Building 3.6s (24/24) FINISHED
[...]
 => exporting layers
[...]

$ docker images
REPOSITORY                        TAG       IMAGE ID       CREATED          SIZE
nginx-declarative-api-webui       latest    65d93e68ab9f   1 minutes ago    62.4MB
nginx-declarative-api             latest    baa9086d4779   1 minutes ago    123MB
nginx-declarative-api-devportal   latest    6df48ac0c209   1 minutes ago    400MB
```

## How to run

1. Start NGINX Declarative API using the provided `nginx-dapi.sh` script
2. Start Postman using the [Postman collection](/contrib/postman)

Starting:

```commandline
$ ./nginx-dapi.sh -c start
-> Deploying NGINX Declarative API
   NGINX Declarative API port: 5000
   Web UI port: 3000
   Developer Portal port: 5001
   Redis port: 6379
[+] Building 0.0s (0/0)
[+] Running 5/5
 ✔ Network nginx-dapi_dapi-network  Created 
 ✔ Container redis                  Started 
 ✔ Container devportal              Started 
 ✔ Container nginx-dapi             Started
 ✔ Container nginx-dapi-webui       Started 
```

Access the Web UI at <http://localhost:3000>

## Local Development Mode

For active development on the Web UI, you can run it locally with hot-reload while keeping the backend services in Docker:

1. **Start backend services only:**

```bash
$ docker-compose -f docker-compose.dev.yaml up -d
[+] Running 4/4
 ✔ Network nginx-dapi_dapi-network  Created 
 ✔ Container redis                  Started 
 ✔ Container devportal              Started 
 ✔ Container nginx-dapi             Started
```

1. **Run Web UI locally:**

```bash
$ cd ../../webui
$ npm install  # first time only
$ npm run dev

NGINX Declarative API Web UI
  ➜  Local:   http://localhost:3000/
```

The Vite dev server automatically proxies API requests to the containerized backend on `localhost:5000`.

**Using custom ports:**

If you started the backend with a custom DAPI port (e.g., `-a 8088`), you need to set the corresponding environment variable for the webui:

```bash
$ ./nginx-dapi.sh -c start -m dev -a 8088

# Then in the webui directory:
$ cd ../../webui
$ VITE_DAPI_PORT=8088 npm run dev
```

Or use the script with default ports:

```bash
$ ./nginx-dapi.sh -c start -m dev

# Then in the webui directory:
$ cd ../../webui
$ npm run dev  # Defaults to port 5000
```

**Benefits:**

- ⚡ Fast hot-reload for UI changes
- 🐛 Full browser debugging capabilities
- 🔧 Backend services isolated in containers
- 🔄 Easy to restart individual services

Starting with custom ports (useful when default ports are in use):

```commandline
$ ./nginx-dapi.sh -c start -a 8080 -w 8081 -d 8082 -r 6380
-> Deploying NGINX Declarative API
   NGINX Declarative API port: 8080
   Web UI port: 8081
   Developer Portal port: 8082
   Redis port: 6380
[+] Building 0.0s (0/0)
[+] Running 4/4
 ✔ Network nginx-dapi_dapi-network  Created 
 ✔ Container redis                  Started 
 ✔ Container devportal              Started 
 ✔ Container nginx-dapi             Started
 ✔ Container nginx-dapi-webui       Started 
```

Stopping:

```commandline
$ ./nginx-dapi.sh -c stop
-> Undeploying NGINX Declarative API
[+] Running 5/5
 ✔ Container nginx-dapi-webui       Removed
 ✔ Container nginx-dapi             Removed 
 ✔ Container devportal              Removed 
 ✔ Container redis                  Removed 
 ✔ Network nginx-dapi_dapi-network  Removed 
```
