# Architecture

This document describes the system architecture, rendering pipeline, and operational workflows of the **NGINX Declarative API**.

> For a feature overview, quickstart examples, and deployment instructions, see [README.md](/README.md).

## Table of Contents

- [System Overview](#system-overview)
  - [Key Components](#key-components)
- [Configuration Rendering Pipeline](#configuration-rendering-pipeline)
- [API Gateway Runtime Request Flow](#api-gateway-runtime-request-flow)
- [GitOps Autosync Mode](#gitops-autosync-mode)
- [Concurrent Access and Queueing Mode](#concurrent-access-and-queueing-mode)
- [Related Documentation](#related-documentation)

---

## System Overview

NGINX Declarative API accepts high-level JSON declarations (as well as incremental `PATCH` updates), resolves any external Sources of Truth, compiles complete NGINX Plus configurations and auxiliary artifacts, and publishes staged bundles to your NGINX control plane.

```mermaid
flowchart LR
    subgraph Clients["Clients and Automation"]
        REST["REST Clients"]
        CICD["CI/CD Pipelines"]
        WEBUI["Web UI"]
        MCPC["MCP Client"] --> MCP["MCP Server"]
    end

    subgraph Core["NGINX Declarative API"]
        API["FastAPI Service & Validator"]
        BUILDER["Config Builder & Template Engine"]
        DEVP["Developer Portal Service"]
        REDIS[("Redis Store & Queue")]
        API --> BUILDER
        BUILDER --> DEVP
        API <--> REDIS
        BUILDER <--> REDIS
    end

    subgraph External["External Services"]
        SOT["Source of Truth (Git / HTTP)"]
        THIRDP["3rd-Party Integrations (Moesif)"]
    end

    subgraph Planes["Control and Data Planes"]
        OUTPUT["Output Publisher"]
        NIM["NGINX Instance Manager"]
        N1["NGINX One Console"]
        AGENT1["NGINX Agent"]
        AGENT2["NGINX Agent"]
        NGINX1["NGINX Plus Instances"]
        NGINX2["NGINX Plus Instances"]

        OUTPUT --> NIM --> AGENT1 --> NGINX1
        OUTPUT --> N1 --> AGENT2 --> NGINX2
    end

    REST --> API
    CICD --> API
    WEBUI --> API
    MCP --> API
    BUILDER <--> SOT
    BUILDER <--> THIRDP
    BUILDER --> OUTPUT
```

### Key Components

| Component | Role |
| --- | --- |
| **Clients (`REST`, `CI/CD`, `Web UI`, `MCP Server`)** | Submit full declarations (`POST`), incremental updates (`PATCH`), or natural-language operations (via [`contrib/mcp`](/contrib/mcp) and [`webui`](/webui)) over REST. |
| **FastAPI Service & Validator (`src/main.py`)** | Exposes versioned endpoints (`/v5.5`, `/v5.6`, `/v5.7`), validates declarations against Pydantic schemas, and routes asynchronous `PATCH` requests through the queue manager. |
| **Config Builder & Template Engine** | Resolves external artifacts, parses OpenAPI/Swagger specs, renders NGINX/WAF configuration files and `njs` modules via Jinja2, and packages staged config bundles. |
| **Redis Store & Queue (`src/NcgRedis.py`)** | Stores active declarations, submission job statuses, autosync artifact metadata/timestamps, and serialized asynchronous `PATCH` queues. |
| **Source of Truth (`SOT`)** | External HTTP(S) or Git endpoints hosting OpenAPI/Swagger schemas, F5 WAF for NGINX policies, TLS certificates/keys/chains, snippets, and custom `njs` scripts. |
| **Developer Portal Service (`src/v5_7/DevPortal.py`)** | Builds Redocly developer portal HTML bundles or Backstage catalog YAML manifests from referenced OpenAPI specs. |
| **3rd-Party Integrations** | Instruments API Gateways with external visibility/telemetry providers such as Moesif. |
| **Output Publishers (`NIMOutput` / `NGINXOneOutput`)** | Deploy staged configurations and auxiliary files (`njs`, TLS certs, MIME types) to NGINX Instance Manager instance groups or NGINX One Console config sync groups, where NGINX Agent applies them to NGINX Plus. |

---

## Configuration Rendering Pipeline

In API **v5.7**, every `POST /v5.7/config`, `PATCH /v5.7/config/{configuid}`, or autosync rebuild passes through a deterministic compilation pipeline before publishing:

```mermaid
flowchart TD
    REQ["Declaration JSON (POST / PATCH / Autosync)"]
    PATCH["Incremental Merge (DeclarationPatcher)"]
    SCHEMA["Pydantic Schema Validation (V5_7_NginxConfigDeclaration)"]
    CTX["ConfigBuildContext Initialization (V5_7_ConfigBuilder)"]
    FETCH["Resolve Source of Truth Artifacts (GitOps)"]
    OAS["Parse OpenAPI 2.0 / 3.0 / 3.1 / 3.2 (OpenAPIParser & APIGateway)"]
    RENDER["Render Configs & Auxiliary Files (Jinja2 templates)"]
    PUBLISH["Stage & Publish Bundle (NIMOutput / NGINXOneOutput)"]

    REQ --> PATCH --> SCHEMA --> CTX
    CTX --> FETCH --> OAS --> RENDER --> PUBLISH
```

| Stage | Primary Modules (`src/`) | Output Produced |
| --- | --- | --- |
| **API & Queue Routing** | `main.py`, `v5_7/Asynchronous.py` | Immediate execution or queued submission UID for `/v5.7/config/{configuid}/submission/{submissionuid}` |
| **Patching & Validation** | `v5_7/DeclarationPatcher.py`, `V5_7_NginxConfigDeclaration.py` | Validated `.output` and `.declaration` objects (`v5.7` Pydantic models) |
| **Artifact Fetching & Parsing** | `v5_7/GitOps.py`, `v5_7/OpenAPIParser.py`, `v5_7/APIGateway.py` | Dereferenced OpenAPI paths, operations, parameters, response codes, `requestBody` schemas, and `$ref` definitions |
| **Config & `njs` Generation** | `V5_7_ConfigBuilder.py`, `templates/v5.7/*.tmpl` | `nginx.conf`, `http.conf`, `stream.conf`, server/upstream/map files, `@apigw_proxy_*` internal locations, and `apigw_body_*.js` validators in `auxFiles` |
| **Control Plane Publishing** | `v5_7/NIMOutput.py`, `v5_7/NGINXOneOutput.py`, `v5_7/NIMNAPUtils.py`, `v5_7/NGINXOneNAPUtils.py` | Staged deployment with automatic `ngx_http_js_module` loading when generated body validators are present |

---

## API Gateway Runtime Request Flow

When `api_gateway.enforce_bodies` is enabled (`true` by default) in API v5.7 and an endpoint defines a resolvable OpenAPI request body schema, generated NGINX locations delegate payload validation to NGINX JavaScript (`njs`) before proxying upstream:

```mermaid
sequenceDiagram
    participant Client
    participant Loc as "NGINX API Location"
    participant NJS as "njs Validator (apigw_body_*.js)"
    participant Proxy as "Internal Location (@apigw_proxy_*)"
    participant Upstream

    Client ->> Loc: HTTP Request (method, headers, body)
    Loc ->> Loc: Method & param maps check (enforce_methods / enforce_parameters)

    alt Undocumented method or missing required param
        Loc -->> Client: HTTP 405 / 400
    else Request passes method & header/query checks
        Loc ->> NJS: js_content validate_req_body_*
        NJS ->> NJS: Validate required body, Content-Type & JSON Schema ($ref / OAS)
        alt Body validation fails
            NJS -->> Client: HTTP 400 JSON error
        else Valid payload or non-body method
            NJS ->> Proxy: r.internalRedirect("@apigw_proxy_*")
            Proxy ->> Proxy: Apply strip_uri, auth, headers, cache & proxy_intercept_errors
            Proxy ->> Upstream: proxy_pass upstream request
            Upstream -->> Client: HTTP Response (masked if enforce_response_codes)
        end
    end
```

Endpoints without request body schemas (or deployments with `enforce_bodies: false`) skip the `njs` phase and proxy directly inside the endpoint `location` block.

---

## GitOps Autosync Mode

When `synctime` is configured under `.output.nms.synctime` or `.output.nginxone.synctime`, a background scheduler in `V5_7_CreateConfig.py` periodically polls every HTTP(S)-referenced Source of Truth artifact (OpenAPI specs, F5 WAF policies, TLS certificates/keys/chains, snippets, and `njs` scripts). Any detected upstream change triggers an automatic rebuild and staged deployment.

```mermaid
sequenceDiagram
    participant CICD as "CI/CD Pipeline"
    participant SOT as "Source of Truth"

    box NGINX Declarative API
        participant NDAPI as "Scheduler & Config Builder"
        participant DevP as "Developer Portal Service"
        participant Redis
    end

    participant CP as "NIM / NGINX One Console"
    participant Agent as "NGINX Agent"
    participant NGINX as "NGINX Plus"

    CICD ->> SOT: Commit updated schema, policy, cert, or snippet

    loop Every synctime seconds
        NDAPI ->> SOT: Poll referenced artifacts metadata/timestamps
        SOT -->> NDAPI: Latest timestamps & ETags
        NDAPI ->> Redis: Compare with cached artifact state

        alt Updates detected
            NDAPI ->> SOT: Pull updated artifacts
            SOT -->> NDAPI: Updated contents

            opt Developer Portal enabled
                NDAPI ->> DevP: Generate updated portal / catalog
                DevP -->> NDAPI: DevPortal artifacts
            end

            NDAPI ->> NDAPI: Rebuild staged NGINX config & njs validators
            NDAPI ->> CP: Publish staged config bundle
            CP ->> Agent: Distribute updated config
            Agent ->> NGINX: Reload NGINX Plus
            CP -->> NDAPI: Deployment outcome
            NDAPI ->> Redis: Persist updated config state & timestamps
        end
    end
```

---

## Concurrent Access and Queueing Mode

For CI/CD pipelines issuing concurrent updates against a shared configuration (`PATCH /v5.7/config/{configuid}`), setting `.output.synchronous` to `false` switches updates to Redis-backed queued execution. Callers receive a submission identifier immediately and can poll `GET /v5.7/config/{configuid}/submission/{submissionuid}` for completion status.

```mermaid
sequenceDiagram
    participant CICD as "CI/CD Pipelines"
    participant API as "FastAPI Endpoint"
    participant Redis as "Redis Queue & Status Store"
    participant Worker as "Queue Manager Worker"
    participant CP as "NIM / NGINX One Console"
    participant NGINX as "NGINX Agent & NGINX Plus"

    Note over CICD,NGINX: Initial baseline deployment (POST /v5.7/config)
    CICD ->> API: POST /v5.7/config
    API ->> CP: Publish initial staged config
    CP ->> NGINX: Apply config to target group
    CP -->> API: Return outcome
    API -->> CICD: Return configUid & status

    Note over CICD,NGINX: Concurrent asynchronous updates (synchronous: false)
    CICD ->> API: PATCH /v5.7/config/{configUid} (Update 1)
    API ->> Redis: Enqueue Update 1 (submissionUid 1)
    API -->> CICD: HTTP 202 Accepted (submissionUid 1)

    CICD ->> API: PATCH /v5.7/config/{configUid} (Update 2)
    API ->> Redis: Enqueue Update 2 (submissionUid 2)
    API -->> CICD: HTTP 202 Accepted (submissionUid 2)

    loop Serialized Queue Processing
        Worker ->> Redis: Dequeue next pending PATCH
        Worker ->> Worker: Apply DeclarationPatcher & rebuild staged config
        Worker ->> CP: Publish staged config
        CP ->> NGINX: Apply updated config
        CP -->> Worker: Return outcome
        Worker ->> Redis: Store completion status & timestamp
    end

    CICD ->> API: GET /v5.7/config/{configUid}/submission/{submissionUid}
    API ->> Redis: Read submission status
    Redis -->> API: Completed / pending status
    API -->> CICD: JSON submission status response
```

---

## Related Documentation

- [README.md](/README.md) — Overview, outcome-driven examples, GitOps & API Gateway use cases, deployment, and testing
- [FEATURES.md](/FEATURES.md) — Complete feature matrix, Request Body Schema Validation reference, and OAS support details
- [USAGE-v5.7.md](/USAGE-v5.7.md) — REST endpoints and JSON schema reference for API `v5.7`
