# NGINX-Declarative-API

[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![codecov](https://codecov.io/gh/f5devcentral/NGINX-Declarative-API/branch/main/graph/badge.svg)](https://codecov.io/gh/f5devcentral/NGINX-Declarative-API)

**NGINX Declarative API** builds and deploys complete NGINX configurations from a single **declarative JSON** describing your **intended outcome** — replacing manual `nginx.conf` authoring and imperative control-plane scripts with an API built for CI/CD, GitOps, and automated API Gateway delivery.

It targets both [F5 NGINX Instance Manager](https://docs.nginx.com/nginx-instance-manager/) (instance groups) and [F5 NGINX One Console](https://docs.nginx.com/nginx-one-console/) (config sync groups).

---

## Quick Navigation

- [Why Use the NGINX Declarative API?](#why-use-the-nginx-declarative-api)
- [Describe the Intended Outcome](#describe-the-intended-outcome)
- [Core Use Cases](#core-use-cases)
  - [GitOps Workflows](#gitops-workflows)
  - [API Gateway Automation](#api-gateway-automation)
  - [Additional Capabilities](#additional-capabilities)
- [Supported Releases](#supported-releases)
- [Architecture](#architecture)
- [Natural-Language Automation (MCP Server)](#natural-language-automation-mcp-server)
- [How to Use](#how-to-use)

---

## Why Use the NGINX Declarative API?

- ✅ **Declarative Simplicity**: Express configurations as a single, high-level JSON object describing the intended outcome.
- ✅ **Automation-First Design**: Integrate configurations into CI/CD pipelines with minimal effort.
- ✅ **Error Reduction**: Built-in schema validation for accurate, consistent, and optimized configurations.
- ✅ **Dynamic Updates**: Handle frequent configuration changes cleanly across dynamic environments (including concurrent async `PATCH` queueing).
- ✅ **Seamless Scalability**: Simplify managing NGINX configurations across large-scale distributed instance groups and config sync groups.
- ✅ **MCP Server**: Configure and manage NGINX using natural language via [contrib/mcp](/contrib/mcp).

> **GitOps integration is built in:** referenced external Sources of Truth (F5 WAF for NGINX policies, TLS certificates/keys/chains/bundles, Swagger/OpenAPI definitions, configuration snippets, and `njs` modules) are checked for updates and NGINX configurations are automatically kept in sync.

---

## Describe the Intended Outcome

Instead of writing NGINX directives step by step (`upstream`, `map`, `location`, `proxy_pass`, TLS blocks, WAF rules), you declare **what outcome NGINX should deliver** in two top-level sections:

- **`.output`** — *Where and how to publish*: target control plane (`nms` or `nginxone`), instance group / config sync group, NGINX Plus license settings, GitOps polling interval (`synctime`), and synchronous vs. queued async `PATCH` execution.
- **`.declaration`** — *What NGINX should enforce and serve*: HTTP/stream servers and upstreams, TLS certificates, authentication/authorization policies, F5 WAF for NGINX policies, and OpenAPI-driven API Gateway routes.

```json
{
  "output": {
    "type": "nms",
    "nms": {
      "url": "https://nim.example.com",
      "instancegroup": "prod-apigw",
      "synctime": 60
    }
  },
  "declaration": {
    "http": {
      "servers": [
        {
          "name": "api_edge",
          "names": ["api.example.com"],
          "locations": [
            {
              "uri": "/v1",
              "apigateway": {
                "openapi_schema": {
                  "content": "https://gitops.example.com/specs/orders-openapi.yaml"
                },
                "api_gateway": {
                  "enabled": true,
                  "strip_uri": true,
                  "enforce_methods": true,
                  "enforce_bodies": true,
                  "enforce_parameters": true,
                  "enforce_response_codes": true
                }
              }
            }
          ]
        }
      ]
    }
  }
}
```

From that single declaration, NGINX Declarative API fetches the referenced OpenAPI spec from your Source of Truth, generates upstream blocks, locations, regex/map validation rules, and SSL/routing directives, publishes them to NGINX Instance Manager, and keeps everything synchronized every `60` seconds.

---

## Core Use Cases

### GitOps Workflows

Keep NGINX configurations continuously synchronized with external **Source of Truth** repositories (Git HTTP endpoints or artifact servers) without re-submitting declarations on every content change:

- **Dynamic Source of Truth Resolution** — Reference remote URLs (or supply inline base64) for:
  - Swagger / OpenAPI specifications
  - F5 WAF for NGINX policies (with version tags and DevSecOps CI/CD workflows)
  - TLS certificates, private keys, CA chains/bundles, and mTLS certificates
  - `http` and `stream` configuration snippets, upstreams, servers, and locations
  - NGINX JavaScript (`njs`) modules
- **Autonomous GitOps Autosync (`synctime`)** — Periodically poll referenced external artifacts; when an updated policy, certificate, or OpenAPI schema is detected, configurations are rebuilt and republished automatically.
- **Concurrent CI/CD Pipelines (`synchronous: false`)** — Safe asynchronous `PATCH` queueing lets multiple teams or pipelines update HTTP servers, upstreams, stream servers, or WAF policies concurrently with submission tracking (`GET /v5.7/config/{configUid}/submission/{submissionUid}`).

### API Gateway Automation

Automatically provision NGINX Plus as an API Gateway directly from your API contracts (see also the blog post: [From OpenAPI to NGINX as an API Gateway using a Declarative API](https://www.f5.com/company/blog/nginx/from-openapi-to-nginx-as-an-api-gateway-using-a-declarative-api)):

- **Broad OpenAPI Specification Support (`v5.7`)** — Ingest YAML or JSON schemas across **OAS 2.0 (Swagger 2.0)**, **OAS 3.0.x**, **OAS 3.1.x**, and **OAS 3.2.x** (including `host`/`basePath`/`schemes`, multiple `servers[]`, per-path/per-operation `servers[]`, server `variables`, `additionalOperations`, and `in: "body"` + `consumes`; see [FEATURES.md](/FEATURES.md) for exact coverage and caveats).
- **Contract-Driven Enforcement** — Enable declarative toggles (`enforce_methods`, `enforce_bodies`, `enforce_parameters`, `enforce_response_codes`) to automatically generate NGINX request/response validation and `map` rules.
- **Per-URI Traffic & Security Controls** — Attach rate limiting, client authentication (JWT, Bearer token, mTLS, OIDC), JWT claim authorization, caching, and logging per API Gateway path subset (`enforceOnPaths`).
- **Zero-Touch Developer Portals** — Automatically generate and publish **Redocly** HTML portals on NGINX Plus or **Backstage.io** YAML catalog manifests alongside your API Gateway.
- **API Visibility** — Integrated **Moesif** instrumentation for API analytics and observability.

### Additional Capabilities

- Full HTTP and Layer 4 (`stream`) load balancing, active healthchecks, cookie-based stickiness, maps, response/request header manipulation, custom access log formats, DNS resolver profiles, ACME TLS automation, and NJS hook bindings (`js_content`, `js_set`, `js_body_filter`, `js_header_filter`, `js_periodic`, `js_preload_object`).
- See [FEATURES.md](/FEATURES.md) for the complete capability matrix across `v5.5`, `v5.6`, and `v5.7`.

---

## Supported Releases

| API Version | F5 NGINX Instance Manager | F5 NGINX One Console | F5 NGINX Plus | F5 WAF for NGINX |
| --- | --- | --- | --- | --- |
| v5.5 | 2.20+ | January 2026 | R33+ | 5.x |
| v5.6 | 2.20+ | January 2026 | R33+ | 5.x |
| v5.7 | 2.22+ | August 2026 | R35+ | 5.x |

> **Note:** F5 NGINX Plus R33 and above [require a valid license](https://docs.nginx.com/solutions/about-subscription-licenses/), configured via `.output.license` in the declarative JSON.

---

## Architecture

Component interactions, **GitOps Autosync Mode**, and **Concurrent Access / Queueing Mode** sequence diagrams are documented in [ARCHITECTURE.md](/ARCHITECTURE.md).

---

## Natural-Language Automation (MCP Server)

[contrib/mcp](/contrib/mcp) provides a **Model Context Protocol (MCP)** server enabling LLM clients (Claude Desktop, Claude Code, or any MCP-compatible client) to create, update, retrieve, delete, and monitor NGINX declarations using natural language — without hand-writing JSON or REST calls.

See the [MCP Server README](/contrib/mcp/README.md) for setup instructions.

---

## How to Use

JSON schema references and endpoint documentation:

- [API v5.7](/USAGE-v5.7.md) — latest
- [API v5.6](/USAGE-v5.6.md) — stable
- [API v5.5](/USAGE-v5.5.md) — deprecated

Sample requests and ready-to-run API Gateway / GitOps examples are available in the [Postman collection](/contrib/postman).

---

## 🏃 How to Run

NGINX Declarative API can be deployed on:

- Linux virtual machine using [docker-compose](/contrib/docker-compose)
- Kubernetes using [manifests](/contrib/kubernetes)
- Kubernetes using the [Helm chart](/contrib/helm/nginx-declarative-api)

### Building Docker Images

Docker images can be built and run using the [docker-compose](/contrib/docker-compose) setup provided.

### REST API Documentation

When running, interactive API documentation is exposed at:

- Swagger UI: `/docs`
- ReDoc UI: `/redoc`
- OpenAPI specification: `/openapi.json`

---

## 🧪 Running Unit Tests

Python unit tests cover schema parsing, config building, and declaration patching:

```bash
pip3 install pytest pyyaml
python3 -m pytest tests/ -v
```

WebUI tests use [Vitest](https://vitest.dev/) and run from `webui/`:

```bash
cd webui
npm install
npm test -- --run
```

Both suites run automatically in GitHub Actions on pull requests and release builds.

---

## 🔒 Security, License & Community

- **Security:** Do **not** open a public GitHub issue for vulnerabilities — follow the responsible disclosure process in [SECURITY.md](/SECURITY.md).
- **License:** Apache License, Version 2.0 — see [LICENSE.md](/LICENSE.md).
- **Support:** Open a GitHub issue (community supported).
- **Contributing:** See [CONTRIBUTING.md](/CONTRIBUTING.md).
- **Code of Conduct:** See [code_of_conduct.md](/code_of_conduct.md).
