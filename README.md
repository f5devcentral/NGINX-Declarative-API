# NGINX-Declarative-API

This tool provides a set of declarative REST API for NGINX Management Suite.

It can be used to manage NGINX Plus configuration lifecycle and to create NGINX Plus configurations using JSON service definitions.

GitOps integration is supported when used with NGINX Management Suite / NGINX Instance Manager: source of truth is checked for updates (NGINX App Protect policies, TLS certificates, keys and chains/bundles) and NGINX configurations are automatically kept in sync.

Use cases include:

- Rapid configuration generation and templating
- CI/CD integration with NGINX Instance Manager (instance groups and staged configs)
- GitOps integration with source of truth support for
  - NGINX App Protect WAF policies
  - TLS certificates, keys and chains/bundles
  - `http` snippets, upstreams, servers, locations
  - `stream` snippets, upstreams, servers

## Architecture

```mermaid
graph TD
DEVOPS([DevOps]) -- REST API --> CICD
User([User]) -- REST API --> NCG
CICD(CI/CD Pipeline) -- REST API --> NCG[[NGINX Declarative API]]
NCG -- Staged Configs --> NIM(NGINX Instance Manager)
NCG -- REST API --> Generic(Generic REST API endpoint)
NCG -- AutoSync / GitOps --> CICD
NIM -- REST API --> NGINX(NGINX Plus) & NGINXOSS(NGINX OSS)
NCG -- ConfigMap --> K8S(Kubernetes)
REDIS[[Redis backend]] --> NCG
NCG --> REDIS
```

## GitOps

```mermaid
sequenceDiagram

title GitOps with NGINX Instance Manager

User ->> GitLab: Push policy update
NGINX Declarative API ->> GitLab: Check for updates
GitLab ->> NGINX Declarative API: Latest timestamp

NGINX Declarative API->> NGINX Declarative API: If updates available
NGINX Declarative API->> GitLab: Fetch updated policies
GitLab ->> NGINX Declarative API : Updated policies

NGINX Declarative API->> NGINX Declarative API: Build staged config
NGINX Declarative API->> NGINX Instance Manager: POST staged config to instance group

NGINX Instance Manager ->> NGINX: Publish config to NGINX instances
```

## Branches

Two branches are currently available:

- [Python](https://github.com/fabriziofiorucci/NGINX-Declarative-API/tree/main) - Main branch, actively developed
- [Node.js](https://github.com/fabriziofiorucci/NGINX-Declarative-API/tree/nodejs) - Not actively developed, kept here for archival purposes

## Input formats

- [X] Declarative REST API

## Output formats

- [X] Plaintext
- [X] JSON-wrapped Base64-encoded
- [X] Kubernetes Configmap
- [X] POST to Generic REST API endpoint
- [X] Output to NGINX Instance Manager 2.1.0+ imperative REST API
  
## Supported NGINX Plus features

| Feature | API v1 | API v2                                                                                            | Notes |
| --------| ------ |---------------------------------------------------------------------------------------------------| ----- |
| Upstreams | X | Per-upstream CRUD                                                                                 | Snippets supported: static and from source of truth |
| HTTP servers | X | Per-server CRUD                                                                                   | Snippets supported (`http`, `servers`, `locations`, `upstreams`: static and from source of truth |
| TCP/UDP servers | X | Per-server CRUD                                                                                   | Snippets supported (`streams`, `servers`, `upstreams`: static and from source of truth |
| TLS | X | Per-TLS configuration CRUD                                                                        | Certificates, keys, chains can be dynamically fetched from source of truth |
| Rate limiting | X | X                                                                                                 | |
| Active healthchecks | X | X                                                                                                 | |
| Cookie-based stickiness | X | X                                                                                                 | |
| Maps | X | X                                                                                                 | |
| NGINX Plus REST API access | X | X                                                                                                 | |
| NGINX App Protect WAF | policies & log formats at `server` and `location` level | Per-policy CRUD at `server` and `location` level with dataplane-based bundle compilation | Security policies can be dynamically fetched from source of truth | 

## How to use

Usage details and JSON schema are available here:
- [API v1](/USAGE-v1.md) - deprecated
- [API v2](/USAGE-v2.md)

A sample Postman collection and usage instructions can be found [here](/contrib/postman)

### Using docker-compose

This is the recommended method to run NGINX Declarative API on a Linux virtual machine. Refer to [installation instructions](https://github.com/fabriziofiorucci/NGINX-Declarative-API/tree/main/contrib/docker-compose)

### As a Python application

This repository has been tested with and requires Python 3.9 or newer.
A running instance of [redis](https://redis.io/) is required: redis host and port can be configured in the `config.toml` file.

Run NGINX Declarative API using:

```
$ git clone https://github.com/fabriziofiorucci/NGINX-Declarative-API
$ cd NGINX-Declarative-API/src
$ pip install -r requirements.txt
$ python3 main.py
```

### As a Docker image

The docker image can be built and run using:

```
$ git clone https://github.com/fabriziofiorucci/NGINX-Declarative-API
$ cd NGINX-Declarative-API
$ docker build -t nginx-declarative-api:latest -f contrib/docker/Dockerfile .
$ docker run --name nginx-declarative-api -d -p 5000:5000 nginx-declarative-api:latest
```

Pre-built docker images are available on Docker Hub and can be run using:

```
$ docker run --name nginx-declarative-api -d -p 5000:5000 <IMAGE_NAME>
```

Available images are:

| Image name                            | Architecture | API version | Notes      |
|---------------------------------------| ------------ |-------------|------------|
| fiorucci/nginx-declarative-api:v1     | linux/amd64  | v1          | Deprecated |
| fiorucci/nginx-declarative-api:latest | linux/amd64  | v1, v2      | Latest     |

Pre-built images are configured to access the redis instance on host:port `redis:6379`. This can be changed by mounting a custom `config.toml` file on the nginx-dapi container.

## REST API documentation

When NGINX Declarative API is running, REST API documentation can be accessed at:

- Documentation and testing: http://127.0.0.1:5000/docs
- Redoc documentation: http://127.0.0.1:5000/redoc
- OpenAPI specification: http://127.0.0.1:5000/openapi.json
