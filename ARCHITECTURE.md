# Architecture

This document describes the high-level architecture and operational workflows of the **NGINX Declarative API**.

> For a feature overview, GitOps & API Gateway use cases, and quickstart instructions, see [README.md](/README.md).

---

## System Overview

The NGINX Declarative API translates a single high-level JSON declaration describing your intended outcome into validated NGINX configurations, auxiliary files, Developer Portal artifacts, and control plane deployments.

```mermaid
---
title: NGINX Declarative API architecture
---
stateDiagram-v2
    Client: **REST Client**
    Pipeline: **CI/CD Pipeline**
    NIM: NGINX Instance Manager
    N1: NGINX One Console
    AGENT1: NGINX Agent
    NGINX1: NGINX
    AGENT2: NGINX Agent
    NGINX2: NGINX
    SOT: Source of Truth
    NDAPI: NGINX Declarative API
    DEVP: Developer Portal Service
    OUTPUT: Output
    REDIS: Redis
    3RDPARTY: 3rd Party integrations
    MCP: MCP Server
    MCPC: **MCP Client**

    MCPC --> MCP
    MCP --> NDAPI
    Pipeline --> NDAPI
    Client --> NDAPI
    NDAPI --> OUTPUT
    NDAPI --> SOT
    SOT --> NDAPI
    NDAPI --> 3RDPARTY
    3RDPARTY --> NDAPI
    NDAPI --> REDIS
    REDIS --> NDAPI
    OUTPUT --> NIM
    OUTPUT --> N1
    NDAPI --> DEVP
    DEVP --> NDAPI
    NIM --> AGENT1
    AGENT1 --> NGINX1
    N1 --> AGENT2
    AGENT2 --> NGINX2
```

### Key Components

| Component | Role |
| --- | --- |
| **Clients (`REST Client`, `CI/CD Pipeline`, `MCP Client`)** | Submit declarative JSON payloads, incremental `PATCH` updates, or natural-language operations (via the [MCP Server](/contrib/mcp)) over REST. |
| **NGINX Declarative API** | Validates declarations against versioned Pydantic schemas, fetches external references, renders NGINX/WAF configurations, and manages publishing workflows. |
| **Source of Truth (`SOT`)** | External HTTP(S)/GitOps endpoints hosting OpenAPI/Swagger specs, F5 WAF policies, TLS certificates/keys/chains, snippets, and `njs` scripts. |
| **Redis** | Persists declaration state, submission statuses, timestamps/metadata for GitOps autosync, and the asynchronous request queue. |
| **Developer Portal Service** | Generates API developer portal artifacts (Redocly HTML bundles or Backstage manifests) from imported OpenAPI schemas. |
| **3rd Party Integrations** | Integrates external tooling such as API visibility backends (Moesif). |
| **Output (`NGINX Instance Manager` / `NGINX One Console`)** | Publishes staged configurations and auxiliary files to target instance groups or config sync groups, where **NGINX Agent** applies them to **NGINX** instances. |

---

## GitOps Autosync Mode

When `synctime` is configured under `.output.nms.synctime` or `.output.nginxone.synctime`, NGINX Declarative API periodically checks all HTTP(S)-referenced Source of Truth artifacts (OpenAPI/Swagger schemas, F5 WAF for NGINX policies, TLS certificates/keys/chains, configuration snippets, and `njs` files). Whenever an upstream artifact changes, configurations are rebuilt and republished automatically without manual API calls.

```mermaid
sequenceDiagram

title GitOps autosync operations

participant CI/CD Pipeline
participant Source of Truth
participant NGINX Declarative API
participant Redis
participant Developer Portal Service
participant NGINX Instance Manager / NGINX One Console
participant NGINX

box NGINX Declarative API
    participant NGINX Declarative API
    participant Developer Portal Service
    participant Redis
end

CI/CD Pipeline ->> Source of Truth: Commit object updates

critical Run every "synctime" seconds

NGINX Declarative API ->>+ Source of Truth: Check for referenced objects updates
Source of Truth ->>- NGINX Declarative API: Latest timestamp

Note over NGINX Declarative API, Redis: data synchronization

option If updates available
NGINX Declarative API ->>+ Source of Truth: Pull updated objects
Source of Truth ->>- NGINX Declarative API: Updated objects

critical Build Staged Config
critical If Developer Portal enabled
    NGINX Declarative API ->>+ Developer Portal Service: DevPortal generation request
    Developer Portal Service ->>- NGINX Declarative API: DevPortal definition
end
end

NGINX Declarative API ->>+ NGINX Instance Manager / NGINX One Console: Publish staged config to instance group / config sync group
NGINX Instance Manager / NGINX One Console ->> NGINX: Publish config to NGINX instances
NGINX Instance Manager / NGINX One Console ->>- NGINX Declarative API: Return outcome

Note over NGINX Declarative API, Redis: data synchronization

end
```

---

## Concurrent Access and Queueing Mode

For concurrent CI/CD pipelines updating a shared configuration via `PATCH`, setting `.output.<target>.synchronous` to `false` switches submissions to asynchronous queued execution. Requests are serialized by the internal queue manager and callers can poll `GET /v5.7/config/{configUid}/submission/{submissionUid}` for completion status.

```mermaid
sequenceDiagram

title Concurrent access and queueing mode

participant CI/CD Pipeline
participant NGINX Declarative API
participant NGINX Instance Manager / NGINX One Console
participant NGINX

critical Initial configuration deployment

CI/CD Pipeline ->> NGINX Declarative API: POST request - base configuration deployment

NGINX Declarative API ->>+ NGINX Instance Manager / NGINX One Console: Publish staged config to instance group / config sync group
NGINX Instance Manager / NGINX One Console ->> NGINX: Publish config to NGINX instances
NGINX Instance Manager / NGINX One Console ->>- NGINX Declarative API: Return outcome

NGINX Declarative API ->> CI/CD Pipeline: Response

end

critical Asynchronous configuration submission

CI/CD Pipeline ->> NGINX Declarative API: PATCH request - asynchronous configuration update 1
NGINX Declarative API ->>+ NGINX Declarative API: request added to the queue
CI/CD Pipeline ->> NGINX Declarative API: PATCH request - asynchronous configuration update 2
NGINX Declarative API ->>+ NGINX Declarative API: request added to the queue


loop Queue Manager Thread
autonumber 1

NGINX Declarative API ->>+ NGINX Declarative API: get configuration update request from queue

NGINX Declarative API ->>+ NGINX Instance Manager / NGINX One Console: Publish staged config to instance group / config sync group
NGINX Instance Manager / NGINX One Console ->> NGINX: Publish config to NGINX instances
NGINX Instance Manager / NGINX One Console ->>- NGINX Declarative API: Return outcome
NGINX Declarative API ->> NGINX Declarative API: Update configuration update request status

autonumber off
end

CI/CD Pipeline ->> NGINX Declarative API: Check configuration request status
NGINX Declarative API ->> CI/CD Pipeline: Response

end
```

---

## Related Documentation

- [README.md](/README.md) — Overview, outcome-driven examples, GitOps & API Gateway use cases, deployment, and testing
- [FEATURES.md](/FEATURES.md) — Complete feature matrix across API versions and OpenAPI specification support
- [USAGE-v5.7.md](/USAGE-v5.7.md) — Declaration schema reference and REST endpoints for API v5.7
