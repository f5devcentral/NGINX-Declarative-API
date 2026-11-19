# NGINX Declarative API v5.7 Usage Guide

API **v5.7** targets:

- [F5 NGINX Instance Manager](https://docs.f5.com/nginx-instance-manager/) `2.22+`
- [F5 NGINX One Console](https://docs.f5.com/nginx-one-console/)
- [F5 NGINX Plus](https://docs.f5.com/nginx/) `R37+`
- [F5 WAF for NGINX](https://docs.f5.com/waf/) with precompiled [policy bundles](https://docs.f5.com/nginx-app-protect-waf/configure/compiler/)

The full JSON Schema is served live at `GET /v5.7/schema` (and `/docs` for Swagger UI). Ready-to-run API Gateway, WAF, and GitOps examples are available in the [Postman collection](/contrib/postman).

## Table of Contents

- [REST API Endpoints](#rest-api-endpoints)
- [Declaration Schema Reference](#declaration-schema-reference)
  - [Top-Level Output Settings](#top-level-output-settings)
  - [NGINX Plus Licensing](#nginx-plus-licensing)
  - [NGINX Instance Manager Output](#nginx-instance-manager-output)
  - [NGINX One Console Output](#nginx-one-console-output)
  - [Declaration Sections](#declaration-sections)
  - [F5 WAF for NGINX Policies and Log Profiles](#f5-waf-for-nginx-policies-and-log-profiles)
  - [TLS Certificates and Keys](#tls-certificates-and-keys)
  - [API Gateway Locations](#api-gateway-locations)
- [Quickstart Examples](#quickstart-examples)

---

## REST API Endpoints

| Method | Endpoint | Purpose | Notes |
| --- | --- | --- | --- |
| `GET` | `/v5.7/schema` | Retrieve the v5.7 JSON Schema | Generated from `ConfigDeclaration` Pydantic models |
| `POST` | `/v5.7/config` | Create and publish a new declaration | Returns a generated `configUid` and deployment outcome |
| `PATCH` | `/v5.7/config/{configuid}` | Update an existing declaration incrementally | Supports per-item CRUD for HTTP servers, HTTP upstreams, Stream servers, Stream upstreams, WAF policies, and TLS certificates/keys. Set `.output.synchronous: false` to enqueue updates (`HTTP 202`) |
| `GET` | `/v5.7/config/{configuid}` | Retrieve an existing stored declaration | Returns the current active declaration JSON |
| `GET` | `/v5.7/config/{configuid}/status` | Retrieve the deployment status of a declaration | Returns latest publish status stored in Redis |
| `GET` | `/v5.7/config/{configuid}/submission/{submissionuid}` | Poll an asynchronous `PATCH` submission status | Cleans up the completed Redis submission entry once processed details are returned |
| `DELETE` | `/v5.7/config/{configuid}` | Delete an existing declaration | Stops associated autosync jobs and removes stored state |

---

## Declaration Schema Reference

Every declaration contains two root objects: `.output` (control plane target, sync mode, licensing) and `.declaration` (NGINX Plus configuration model).

### Top-Level Output Settings

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `.output.type` | `string` | *(required)* | Target control plane: `"nms"` (NGINX Instance Manager) or `"nginxone"` (NGINX One Console) |
| `.output.synchronous` | `boolean` | `true` | Applies to `PATCH` requests. When `true`, waits for the control plane deployment response; when `false`, enqueues the update in Redis and returns `HTTP 202` with a `submissionUid` |
| `.output.license` | `object` | `null` | NGINX Plus license reporting configuration |
| `.output.nms` | `object` | `null` | Required when `.output.type` is `"nms"` |
| `.output.nginxone` | `object` | `null` | Required when `.output.type` is `"nginxone"` |

### NGINX Plus Licensing

Configuration under `.output.license`:

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `.output.license.endpoint` | `string` | `"product.connect.nginx.com"` | Usage reporting endpoint (can point to NGINX Instance Manager FQDN/IP) |
| `.output.license.token` | `string` | `""` | JWT license token. When omitted, an existing `/etc/nginx/license.jwt` on the instance is preserved untouched |
| `.output.license.ssl_verify` | `boolean` | `true` | Set to `false` to skip TLS verification when reporting without a local PKI (not recommended for production) |
| `.output.license.grace_period` | `boolean` | `false` | Set to `true` to enable the 180-day usage reporting grace period |
| `.output.license.proxy` | `string` | `""` | Optional explicit forward proxy (`IP:port` or `FQDN:port`) for license reporting |
| `.output.license.proxy_username` | `string` | `""` | Optional forward proxy authentication username |
| `.output.license.proxy_password` | `string` | `""` | Optional forward proxy authentication password |

### NGINX Instance Manager Output

Configuration under `.output.nms`:

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `.output.nms.url` | `string` | *(required)* | NGINX Instance Manager base URL |
| `.output.nms.username` | `string` | `""` | Authentication username |
| `.output.nms.password` | `string` | `""` | Authentication password |
| `.output.nms.instancegroup` | `string` | `""` | Target instance group name for staged config deployment |
| `.output.nms.synctime` | `integer` | `0` | GitOps autosync poll interval in seconds. When `> 0`, external HTTP(S) Source of Truth references (OpenAPI schemas, WAF policies, TLS certs/keys, snippets, `njs`) are polled and automatically republished on change |
| `.output.nms.modules` | `string[]` | `[]` | Dynamic NGINX modules to load (e.g., `"ngx_http_app_protect_module"`, `"ngx_http_js_module"`, `"ngx_stream_js_module"`). Note: `ngx_http_js_module` is added automatically if OpenAPI request body schema enforcement generates `njs` validators |

### NGINX One Console Output

Configuration under `.output.nginxone`:

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `.output.nginxone.url` | `string` | *(required)* | NGINX One Console base URL |
| `.output.nginxone.namespace` | `string` | `""` | Target NGINX One namespace |
| `.output.nginxone.token` | `string` | `""` | API authentication token |
| `.output.nginxone.configsyncgroup` | `string` | `""` | Target config sync group name |
| `.output.nginxone.synctime` | `integer` | `0` | GitOps autosync poll interval in seconds for external HTTP(S) Source of Truth references |
| `.output.nginxone.modules` | `string[]` | `[]` | Dynamic NGINX modules to load (`ngx_http_js_module` is added automatically when OpenAPI body validators are generated) |

### Declaration Sections

Top-level keys under `.declaration`:

| Field | Type | Description |
| --- | --- | --- |
| `.declaration.http` | `object` | HTTP servers, locations, API Gateways, upstreams, maps, caches, log formats, `njs` hooks/profiles, ACME issuers, WAF policies, and WAF log profiles |
| `.declaration.layer4` | `object` | TCP/UDP (`stream`) servers and upstreams |
| `.declaration.resolvers[]` | `object[]` | DNS resolver profiles referenced by HTTP servers/upstreams or Layer 4 upstreams |
| `.declaration.certificates[]` | `object[]` | TLS certificates and private keys |
| `.declaration.authentication` | `object` | Client (`.client[]`: JWT, mTLS, OIDC) and upstream/Source-of-Truth (`.server[]`: Bearer, Basic, header, mTLS) authentication profiles |
| `.declaration.authorization[]` | `object[]` | JWT claims client authorization profiles |

> For detailed profile JSON schemas and feature availability across `v5.5`–`v5.7`, see [FEATURES.md](/FEATURES.md).

### F5 WAF for NGINX Policies and Log Profiles

Configured under `.declaration.http.policies[]` and `.declaration.http.log_profiles[]`:

| Field | Type | Default / Allowed | Description |
| --- | --- | --- | --- |
| `.policies[].type` | `string` | `"app_protect"` | Policy engine type |
| `.policies[].name` | `string` | `""` | Policy name (must match the policy name inside the WAF policy JSON file) |
| `.policies[].active_tag` | `string` | `""` | Version tag to activate (e.g., `"v1"`) |
| `.policies[].versions[]` | `object[]` | `[]` | Available policy versions (`tag`, `displayName`, `description`, `contents` as base64 or HTTP(S) URL) |
| `.log_profiles[].type` | `string` | `"app_protect"` | WAF log profile type |
| `.log_profiles[].app_protect` | `object` | `null` | F5 WAF security log settings (`name`, `format`: `"default" \| "grpc" \| "arcsight" \| "splunk" \| "user-defined"`, `type`: `"all" \| "illegal" \| "blocked"`, `format_string`, size limits) |

### TLS Certificates and Keys

Configured under `.declaration.certificates[]`:

| Field | Type | Allowed | Description |
| --- | --- | --- | --- |
| `.certificates[].type` | `string` | `"certificate"`, `"key"` | Asset type |
| `.certificates[].name` | `string` | *(required)* | Asset name without directory path or extension (e.g., `"test-application"`) |
| `.certificates[].contents` | `object` | `null` | Source of Truth reference (`content` as base64 or HTTP(S) URL, with optional authentication) |

### API Gateway Locations

Configured under `.declaration.http.servers[].locations[].apigateway`:

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `.openapi_schema` | `object` | `null` | Base64-encoded OpenAPI/Swagger specification or remote HTTP(S) URL (YAML or JSON; OAS `2.0`, `3.0.x`, `3.1.x`, `3.2.x`) |
| `.api_gateway.enabled` | `boolean` | `false` | Enables API Gateway provisioning for the location |
| `.api_gateway.strip_uri` | `boolean` | `false` | Strips the location `uri` prefix before forwarding upstream |
| `.api_gateway.server_url` | `string` | `""` | Base destination URL of the upstream server (fallback when OpenAPI `servers` are absent or overridden) |
| `.api_gateway.enforce_methods` | `boolean` | `true` | Restricts requests to documented HTTP methods |
| `.api_gateway.enforce_bodies` | `boolean` | `true` | Enforces required request bodies, `Content-Type`, and OpenAPI/JSON Schema payload structure (via auto-generated `njs` validators) |
| `.api_gateway.enforce_parameters` | `boolean` | `true` | Enforces required query parameters, header parameters, and allowed `enum` values |
| `.api_gateway.enforce_response_codes` | `boolean` | `true` | Intercepts undocumented upstream HTTP status codes |
| `.authentication` / `.authorization` / `.cache` / `.rate_limit` | `object` / `array` | — | Path-scoped policies controlled with `enforceOnPaths` and `paths` |
| `.developer_portal` / `.visibility` | `object` / `array` | — | Redocly/Backstage developer portal and Moesif visibility integrations |

---

## Quickstart Examples

<details>
<summary>Example: <code>POST /v5.7/config</code> publishing an OpenAPI-driven API Gateway with GitOps autosync</summary>

```json
{
  "output": {
    "type": "nms",
    "nms": {
      "url": "https://nim.example.com",
      "username": "admin",
      "password": "<PASSWORD>",
      "instancegroup": "prod-apigw",
      "synctime": 60
    }
  },
  "declaration": {
    "http": {
      "servers": [
        {
          "name": "petstore_gw",
          "names": ["api.example.com"],
          "locations": [
            {
              "uri": "/v1",
              "apigateway": {
                "openapi_schema": {
                  "content": "https://gitops.example.com/specs/petstore-openapi.yaml"
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

</details>

<details>
<summary>Example: Asynchronous <code>PATCH /v5.7/config/{configuid}</code> adding/updating an HTTP upstream</summary>

```json
{
  "output": {
    "type": "nms",
    "synchronous": false,
    "nms": {
      "url": "https://nim.example.com",
      "username": "admin",
      "password": "<PASSWORD>",
      "instancegroup": "prod-apigw"
    }
  },
  "declaration": {
    "http": {
      "upstreams": [
        {
          "name": "backend_pool",
          "origin": [
            { "server": "10.0.1.10:8080" },
            { "server": "10.0.1.11:8080" }
          ]
        }
      ]
    }
  }
}
```

Poll completion via `GET /v5.7/config/{configuid}/submission/{submissionuid}` using the `submissionUid` returned in the `HTTP 202` payload.

</details>
