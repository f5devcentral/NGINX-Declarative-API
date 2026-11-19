# NGINX Declarative API

[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![codecov](https://codecov.io/gh/f5devcentral/NGINX-Declarative-API/branch/main/graph/badge.svg)](https://codecov.io/gh/f5devcentral/NGINX-Declarative-API)

**NGINX Declarative API** builds, validates, and deploys complete NGINX Plus configurations from a single **declarative JSON** describing your **intended outcome**—replacing hand-written `nginx.conf` files and imperative control-plane scripts with an automation-first API designed for CI/CD, GitOps, and OpenAPI-driven API Gateway delivery.

It publishes staged configurations to both [F5 NGINX Instance Manager](https://docs.f5.com/nginx-instance-manager/) (instance groups) and [F5 NGINX One Console](https://docs.f5.com/nginx-one-console/) (config sync groups).

## Table of Contents

- [Why NGINX Declarative API](#why-nginx-declarative-api)
- [Describe the Intended Outcome](#describe-the-intended-outcome)
- [Core Use Cases](#core-use-cases)
  - [API Gateway Automation](#api-gateway-automation)
  - [GitOps Workflows and Autosync](#gitops-workflows-and-autosync)
  - [Traffic Management, Security, and WAF](#traffic-management-security-and-waf)
- [Supported Releases](#supported-releases)
- [Architecture and Ecosystem](#architecture-and-ecosystem)
- [Documentation and Examples](#documentation-and-examples)
- [Deployment](#deployment)
- [Running Tests](#running-tests)
- [Security, License, and Community](#security-license-and-community)

---

## Why NGINX Declarative API

- **Declarative Simplicity:** Model your entire NGINX Plus edge in a single high-level JSON payload instead of managing fragmented configuration templates.
- **Built-In Contract Enforcement:** Generate full API Gateway enforcement directly from Swagger and OpenAPI definitions—covering methods, headers, query parameters, response codes, `Content-Type`, and request body schemas.
- **GitOps-Native Reconciliation:** Reference remote Sources of Truth for OpenAPI specs, F5 WAF for NGINX policies, TLS certificates/keys/chains, snippets, and `njs` modules; keep deployments continuously in sync via `synctime`.
- **Safe Concurrent Delivery:** Queue concurrent `PATCH` updates safely across CI/CD pipelines with asynchronous submission tracking.
- **Natural-Language Automation:** Includes a dedicated [Model Context Protocol (MCP) server](/contrib/mcp) and web UI ([`webui`](/webui)) alongside the REST API.

---

## Describe the Intended Outcome

Instead of writing low-level `upstream`, `map`, `location`, TLS, WAF, or `proxy_pass` blocks manually, every declaration has two clean top-level sections:

| Section | Responsibility | Key Settings |
| --- | --- | --- |
| **`.output`** | *Where and how to publish* | Target control plane (`nms` or `nginxone`), instance group / config sync group, NGINX Plus license, GitOps poll interval (`synctime`), synchronous vs. queued execution |
| **`.declaration`** | *What NGINX should serve and enforce* | HTTP and Layer 4 (`stream`) servers/upstreams, TLS & ACME issuers, auth/authz profiles, F5 WAF for NGINX policies, `njs` hooks, and OpenAPI-driven API Gateways |

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

From that single declaration, NGINX Declarative API fetches the OpenAPI specification, compiles upstream definitions, per-path routing locations, parameter validation `map` rules, and `njs` request body schema validators, publishes the complete bundle to NGINX Instance Manager, and re-checks external artifacts every `60` seconds.

---

## Core Use Cases

### API Gateway Automation

Turn OpenAPI contracts directly into production NGINX Plus API Gateways (see also [From OpenAPI to NGINX as an API Gateway using a Declarative API](https://www.f5.com/company/blog/nginx/from-openapi-to-nginx-as-an-api-gateway-using-a-declarative-api)):

- **Broad OpenAPI Coverage (`v5.7`):** Supports YAML and JSON schemas across **OAS 2.0 (Swagger 2.0)**, **OAS 3.0.x**, **OAS 3.1.x**, and **OAS 3.2.x**, including local `$ref` dereferencing, root/path/operation `servers[]`, server `variables`, `additionalOperations`, and Swagger `in: "body"` + `consumes`.
- **Full Contract Enforcement:**
  - `enforce_methods` — restricts each endpoint to documented HTTP methods.
  - `enforce_bodies` — validates required request body presence, `Content-Type` headers, and full OpenAPI / JSON Schema request payloads (JSON, `*+json`, `application/x-www-form-urlencoded`, and `text/plain`) via auto-generated NGINX JavaScript (`njs`).
  - `enforce_parameters` — validates required query parameters, mandatory HTTP headers, and enumerated values.
  - `enforce_response_codes` — intercepts and normalizes undocumented upstream status codes.
- **Scoped Traffic & Security Policies:** Apply rate limiting, client authentication (JWT, Bearer token, mTLS, OIDC), JWT claim authorization, response caching, and access/error logging across targeted endpoint subsets (`enforceOnPaths`).
- **Developer Portals & Visibility:** Publish integrated **Redocly** portals or **Backstage.io** catalog manifests ([`contrib/devportal`](/contrib/devportal)), and instrument API telemetry with **Moesif**.

### GitOps Workflows and Autosync

Keep edge configurations aligned with Git repositories and external **Sources of Truth** without re-submitting declarations on every upstream change ([`contrib/gitops-examples`](/contrib/gitops-examples)):

- **External Artifact Resolution:** Reference remote URLs (or inline base64 payloads) for OpenAPI specs, F5 WAF for NGINX policies, TLS certificates/keys/CA bundles, configuration snippets, and `njs` scripts.
- **Continuous Autosync (`synctime`):** Periodically poll referenced external artifacts and automatically rebuild and republish NGINX configurations whenever an artifact changes.
- **Concurrent CI/CD Pipelines (`synchronous: false`):** Non-blocking asynchronous `PATCH` queueing lets multiple teams update servers, upstreams, or WAF policies in parallel with live job tracking (`GET /v5.7/config/{configUid}/submission/{submissionUid}`).

### Traffic Management, Security, and WAF

Configure HTTP and Layer 4 (`stream`) upstreams, active health checks, cookie-based stickiness, header rewrites, NGINX maps, custom access log formats, DNS resolver profiles, ACME TLS certificates, custom `njs` hooks, and F5 WAF for NGINX policies and log profiles. See [FEATURES.md](/FEATURES.md) for the complete capability matrix across `v5.5`, `v5.6`, and `v5.7`.

---

## Supported Releases

| API Version | F5 NGINX Instance Manager | F5 NGINX One Console | F5 NGINX Plus | F5 WAF for NGINX |
| :---: | --- | --- | :---: | :---: |
| **`v5.5`** | `2.20+` | January 2026 | `R33+` | `5.x` |
| **`v5.6`** | `2.20+` | January 2026 | `R33+` | `5.x` |
| **`v5.7`** | `2.22+` | August 2026 | `R35+` | `5.x` |

> **License Note:** F5 NGINX Plus `R33+` [requires a valid subscription license](https://docs.f5.com/solutions/about-subscription-licenses/), provided via `.output.license` in your declaration.

---

## Architecture and Ecosystem

- **Architecture Diagrams:** Control-plane flows, **GitOps Autosync Mode**, and **Concurrent Access / Queueing Mode** sequence diagrams are documented in [ARCHITECTURE.md](/ARCHITECTURE.md).
- **Natural-Language Automation (MCP Server):** [contrib/mcp](/contrib/mcp) provides a Model Context Protocol server enabling LLM clients (such as Claude Desktop or Claude Code) to create, update, inspect, delete, and monitor NGINX declarations in plain language. See the [MCP Server README](/contrib/mcp/README.md).
- **Web UI:** Included in [`webui/`](/webui) for visual declaration editing and management.

---

## Documentation and Examples

| Resource | Purpose | Status |
| --- | --- | --- |
| [USAGE-v5.7.md](/USAGE-v5.7.md) | REST endpoints and full JSON schema reference (`v5.7`) | Latest |
| [USAGE-v5.6.md](/USAGE-v5.6.md) | REST endpoints and JSON schema reference (`v5.6`) | Stable |
| [USAGE-v5.5.md](/USAGE-v5.5.md) | REST endpoints and JSON schema reference (`v5.5`) | Deprecated |
| [FEATURES.md](/FEATURES.md) | Full capability matrix, OpenAPI support, and config tables | Current |
| [contrib/postman](/contrib/postman) | Ready-to-run Postman collections for API Gateway, WAF, and GitOps | Examples |
| [contrib/gitops-examples](/contrib/gitops-examples) | Sample GitOps pipelines and external Source of Truth workflows | Examples |

---

## Deployment

NGINX Declarative API can be built and deployed using any of the provided packaging options:

- **Docker / Docker Compose:** [contrib/docker-compose](/contrib/docker-compose) (also builds local container images from [Dockerfile](/Dockerfile))
- **Kubernetes Manifests:** [contrib/kubernetes](/contrib/kubernetes)
- **Helm Chart:** [contrib/helm/nginx-declarative-api](/contrib/helm/nginx-declarative-api)

Once the service is running, interactive REST API documentation is served automatically at:

- **Swagger UI:** `/docs`
- **ReDoc UI:** `/redoc`
- **OpenAPI JSON:** `/openapi.json`

---

## Running Tests

### Python Test Suite

Covers OpenAPI parsing, NGINX configuration & `njs` generation, declaration patching, and utility modules (runtime validation checks for generated `njs` body validators execute automatically when `node` is installed on `PATH`):

```bash
pip3 install -r src/requirements.txt pytest
python3 -m pytest tests/ -v
```

### Web UI Test Suite

Runs [Vitest](https://vitest.dev/) unit tests for [`webui/`](/webui):

```bash
cd webui
npm install
npm test -- --run
```

Both test suites run automatically in GitHub Actions on pull requests and release builds.

---

## Security, License, and Community

- **Security:** Do **not** open public GitHub issues for suspected vulnerabilities—follow the disclosure process in [SECURITY.md](/SECURITY.md).
- **License:** Apache License, Version 2.0 — see [LICENSE.md](/LICENSE.md).
- **Contributing:** Guidelines and workflow details are in [CONTRIBUTING.md](/CONTRIBUTING.md).
- **Support:** Open a GitHub issue (community supported).
- **Code of Conduct:** See [code_of_conduct.md](/code_of_conduct.md).
