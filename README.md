# NGINX-Config-Generator

This tool creates NGINX Plus configuration files for a given JSON service declaration.
GitOps integration is supported when used with NGINX Instance Manager: source of truth is checked for updates (NGINX App Protect policies, TLS certificates, keys and chains/bundles) and NGINX configurations are automatically kept in sync

Use cases include:

- Rapid configuration generation and templating
- CI/CD integration with NGINX Instance Manager (instance groups and staged configs)
- GitOps integration with automated NGINX App Protect policies and TLS certificates, keys and chains/bundles sync

## Architecture

```mermaid
graph TD
DEVOPS([DevOps]) -- REST API --> CICD
User([User]) -- REST API --> NCG
CICD(CI/CD Pipeline) -- REST API --> NCG[[NGINX Config Generator]]
NCG -- Staged Configs --> NIM(NGINX Instance Manager)
NCG -- REST API --> Generic(Generic REST API endpoint)
NCG -- AutoSync / GitOps --> CICD
NIM -- REST API --> NGINX(NGINX Plus) & NGINXOSS(NGINX OSS)
NCG -- ConfigMap --> K8S(Kubernetes)
REDIS[[Redis backend]] --> NCG
NCG --> REDIS
```

## Branches

Two branches are currently available:

- [Python](https://github.com/fabriziofiorucci/NGINX-Config-Generator/tree/main) - Main branch, actively developed
- [Node.js](https://github.com/fabriziofiorucci/NGINX-Config-Generator/tree/nodejs)

## Input formats

- [X] REST API
- [ ] Interactive wizard

## Output formats

- [X] Plaintext
- [X] JSON-wrapped Base64-encoded
- [X] Kubernetes Configmap
- [X] POST to Generic REST API endpoint
- [X] NGINX Instance Manager 2.1.0+ staged config / instance group interoperability
  
## Supported NGINX Plus configurations

- [X] Upstreams
- [X] Servers (HTTP services)
- [X] Servers (TCP & UDP services)
- [X] TLS (HTTP and TCP services) - certificates, keys, chains can be dynamically fetched from source of truth
- [X] Locations
- [X] Rate limiting
- [X] Active healthchecks
- [X] Cookie-based stickiness
- [X] NGINX Plus REST API access
- [X] NGINX App Protect policies and log formats (at `server` and `location` level)  - security policies can be dynamically fetched from source of truth
- [X] Maps (for `http`)
- [X] Custom configuration snippets (for `upstreams`, `servers`, `locations`, `streams`, `http`)
- [ ] Caching

## How to run

### On a Linux Virtual Machine

This repository has been tested with and requires Python 3.9 or newer.
A running instance of [redis](https://redis.io/) is required: redis host and port can be configured in the `config.toml` file.

Run NGINX Config Generator using:

```
$ git clone https://github.com/fabriziofiorucci/NGINX-Config-Generator
$ cd NGINX-Config-Generator/src
$ pip install -r requirements.txt
$ python3 main.py
```

### As a Docker image

The docker image can be built and run using:

```
$ git clone https://github.com/fabriziofiorucci/NGINX-Config-Generator
$ cd NGINX-Config-Generator
$ docker build -t nginx-config-generator:latest -f contrib/docker/Dockerfile .
$ docker run --name nginx-cg -d -p 5000:5000 nginx-config-generator:latest
```

A pre-built docker image is available on Docker Hub and can be run using:

```
$ docker run --name nginx-cg -d -p 5000:5000 fiorucci/nginx-config-generator:latest
```

Usage details and JSON schema are available [here](/USAGE.md)

A sample Postman collection and usage instructions can be found [here](/postman)

## REST API documentation

When NGINX Config Generator is running, REST API documentation can be accessed at:

- Documentation and testing: http://127.0.0.1:5000/docs
- Redoc documentation: http://127.0.0.1:5000/redoc
- OpenAPI specification: http://127.0.0.1:5000/openapi.json
