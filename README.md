# NGINX-Declarative-API

[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)

This project provides a set of declarative REST API for [NGINX Instance Manager](https://docs.nginx.com/nginx-management-suite/nim/) and [NGINX One Cloud Console](https://docs.nginx.com/nginx-one/) (currently in early stage).

It can be used to manage NGINX Plus configuration lifecycle and to create NGINX Plus configurations using JSON service definitions.

GitOps integration is supported: source of truth is checked for updates (NGINX App Protect policies, TLS certificates, keys and chains/bundles, Swagger/OpenAPI definitions, snippets) and NGINX configurations are automatically kept in sync.

Use cases include:

- Rapid configuration generation and templating
- CI/CD integration with NGINX Instance Manager (instance group) and NGINX One Cloud Console (config sync group)
- NGINX App Protect DevSecOps integration (NGINX Instance Manager only)
- API Gateway deployments with automated Swagger / OpenAPI schema import
- API Developer portals zero-touch deployment
- GitOps integration with source of truth support for
  - NGINX App Protect WAF policies
  - TLS certificates, keys and chains/bundles
  - mTLS certificates
  - `http` snippets, upstreams, servers, locations
  - `stream` snippets, upstreams, servers
  - Swagger / OpenAPI schemas
  - NGINX Javascript

A **blog article** to automate NGINX API Gateway management from OpenAPI schemas is available [here](https://www.f5.com/company/blog/nginx/from-openapi-to-nginx-as-an-api-gateway-using-a-declarative-api)

## Supported releases

- NGINX Instance Manager 2.14+
- NGINX One Cloud Console
- NGINX Plus R30+
- NGINX App Protect WAF 4.8+

## Architecture

```mermaid
---
title: NGINX Declarative API architecture
---
stateDiagram-v2
    DevOps: User
    Client: REST Client
    Pipeline: CI/CD Pipeline
    NIM: NGINX Instance Manager
    N1: NGINX One Cloud Console
    AGENT1: NGINX Agent
    NGINX1: NGINX
    AGENT2: NGINX Agent
    NGINX2: NGINX
    INPUT: Input
    SOT: Source of Truth
    NDAPI: NGINX Declarative API Core
    DEVP: Developer Portal Service
    OUTPUT: Output
    REDIS: Redis
    POST: Generic POST endpoint
    CONFIGMAP: Kubernetes ConfigMap
    PLAINTEXT: Plaintext
    BASE64: Base64-encoded

    DevOps --> Pipeline
    Pipeline --> INPUT
    Client --> INPUT
    INPUT --> NDAPI
    NDAPI --> OUTPUT
    NDAPI --> SOT
    SOT --> NDAPI
    NDAPI --> REDIS
    REDIS --> NDAPI
    OUTPUT --> BASE64
    OUTPUT --> POST
    OUTPUT --> CONFIGMAP
    OUTPUT --> PLAINTEXT
    OUTPUT --> NIM
    OUTPUT --> N1
    NDAPI --> DEVP
    DEVP --> NDAPI
    NIM --> AGENT1
    AGENT1 --> NGINX1
    N1 --> AGENT2
    AGENT2 --> NGINX2
```

## GitOps Autosync Mode

```mermaid
sequenceDiagram

title GitOps autosync operations

participant CI/CD Pipeline
participant Source of Truth
participant NGINX Declarative API Core
participant Redis
participant Developer Portal Service
participant NGINX Instance Manager / NGINX One
participant NGINX

box NGINX Declarative API
    participant NGINX Declarative API Core
    participant Developer Portal Service
    participant Redis
end

CI/CD Pipeline ->> Source of Truth: Commit object updates

critical Run every "synctime" seconds

NGINX Declarative API Core ->>+ Source of Truth: Check for referenced objects updates
Source of Truth ->>- NGINX Declarative API Core: Latest timestamp

Note over NGINX Declarative API Core, Redis: data synchronization

option If updates available
NGINX Declarative API Core ->>+ Source of Truth: Pull updated objects
Source of Truth ->>- NGINX Declarative API Core : Updated objects

critical Build Staged Config
critical If Developer Portal enabled
    NGINX Declarative API Core ->>+ Developer Portal Service: DevPortal generation request
    Developer Portal Service ->>- NGINX Declarative API Core: DevPortal definition
end
end

NGINX Declarative API Core ->>+ NGINX Instance Manager / NGINX One: Publish staged config to instance group / config sync group
NGINX Instance Manager / NGINX One ->> NGINX: Publish config to NGINX instances
NGINX Instance Manager / NGINX One ->>- NGINX Declarative API Core: Publish outcome

Note over NGINX Declarative API Core, Redis: data synchronization

end
```

## Input formats

- [X] Declarative JSON

## Output formats

- [X] Plaintext
- [X] JSON-wrapped Base64-encoded
- [X] Kubernetes Configmap
- [X] POST to Generic REST API endpoint
- [X] Output to NGINX Instance Manager 2.14+ imperative REST API (instance group)
- [X] Output to NGINX One Cloud Console REST API (config sync group)
  
## Supported features

See the [features list](/FEATURES.md)

## How to use

Usage details and JSON schema are available here:

- [API v5.1](/USAGE-v5.1.md) - development
- [API v5.0](/USAGE-v5.0.md) - latest
- [API v4.2](/USAGE-v4.2.md)

A sample Postman collection and usage instructions can be found [here](/contrib/postman)

## How to run

NGINX Declarative API can be deployed on a Linux virtual machine using [docker-compose](/contrib/docker-compose) or on [Kubernetes](/contrib/kubernetes)

## Building Docker images

Docker images can be built and run using the Docker compose [script](/contrib/docker-compose) provided

## REST API documentation

When NGINX Declarative API is running, REST API documentation can be accessed at:

- Documentation and testing: `/docs`
- Redoc documentation: `/redoc`
- OpenAPI specification: `/openapi.json`

## License

This repository is licensed under the Apache License, Version 2.0. You are free to use, modify, and distribute this codebase within the terms and conditions outlined in the license. For more details, please refer to the [LICENSE](/LICENSE.md) file.

## Support

For support, please open a GitHub issue. Note that the code in this repository is community supported.

## Contributing

See [Contributing](/CONTRIBUTING.md)

## Code of Conduct

See the [Code of Conduct](/code_of_conduct.md)
