# NGINX-Config-Generator

This tool creates NGINX Plus configuration files for a given JSON service declaration.

Use cases include quick configuration generation and templating.

## Architecture

```mermaid
graph TD
U([User]) -- Terminal --> IW(Interactive wizard)
DEVOPS([DevOps]) -- REST API --> CICD
IW -- REST API --> NCG[NGINX Configuration Generator]
CICD(CI/CD Pipeline) -- REST API --> NCG
NCG -- REST API --> NIM(NGINX Instance Manager)
NCG -- REST API --> Generic(Generic REST API endpoint) & IW & CICD
```

## Branches

Two branches are currently available:

- [Python](https://github.com/fabriziofiorucci/NGINX-Config-Generator)
- [Node.js](https://github.com/fabriziofiorucci/NGINX-Config-Generator)

## Input formats

- [X] REST API
- [ ] Interactive wizard

## Output formats

- [X] Plaintext
- [X] JSON-wrapped Base64-encoded
- [X] Kubernetes Configmap
- [X] POST to Generic REST API endpoint
- [ ] NGINX Instance Manager interoperability
  
## Supported NGINX Plus configurations

- [X] Upstreams
- [X] Servers
- [X] TLS
- [X] Locations
- [X] Rate limiting
- [X] Active healthchecks
- [X] Cookie-based stickiness
- [X] NGINX Plus REST API access
- [X] Custom configuration snippets (for upstreams, servers, locations)
- [ ] Caching

## How to use

Run NGINX Config Generator using:

```
$ cd src
$ pip install -r requirements.txt
$ python3 main.py
```

Usage details and JSON schema are available [here](/USAGE.md)

A sample Postman collection can be found [here](/postman)

## REST API documentation

When NGINX Config Generator is running, REST API documentation can be accessed at:

- Documentation and testing: http://127.0.0.1:5000/docs
- Redoc documentation: http://127.0.0.1:5000/redoc
- OpenAPI specification: http://127.0.0.1:5000/openapi.json
```