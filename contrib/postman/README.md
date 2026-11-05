# NGINX Declarative API (v5.7) — Postman Collection & Environment Guide

This directory contains the comprehensive **Postman Collection v2.1** (`NGINX Declarative API.postman_collection.json`) and its built-in **Collection / Environment Variables** for demonstrating, testing, and automating every capability of the **[NGINX Declarative API v5.7](https://github.com/f5devcentral/NGINX-Declarative-API)**.

---

## Table of Contents

1. [Overview & v5.7 Architecture](#1-overview--v57-architecture)
2. [Summary of Collection Enhancements & Fixes](#2-summary-of-collection-enhancements--fixes)
3. [Quickstart Guide](#3-quickstart-guide)
4. [Collection & Environment Variables Reference](#4-collection--environment-variables-reference)
5. [API v5.7 Endpoints Reference](#5-api-v57-endpoints-reference)
6. [Use-Case Catalog & Folder Walkthroughs](#6-use-case-catalog--folder-walkthroughs)
   - [6.1 Housekeeping - common endpoints](#61-housekeeping---common-endpoints)
   - [6.2 HTTPS server (TLS Offload, WAF, Maps, Caching, Health Checks)](#62-https-server-tls-offload-waf-maps-caching-health-checks)
   - [6.3 ACME Protocol (Automated TLS Certificates)](#63-acme-protocol-automated-tls-certificates)
   - [6.4 HTTP Headers Manipulation](#64-http-headers-manipulation)
   - [6.5 JWT Client Authentication](#65-jwt-client-authentication)
   - [6.6 JWT Client Authentication and Authorization (RBAC)](#66-jwt-client-authentication-and-authorization-rbac)
   - [6.7 mTLS Client Authentication (PKI, CRL, OCSP, Stapling)](#67-mtls-client-authentication-pki-crl-ocsp-stapling)
   - [6.8 OIDC Client Authentication (Per-Location & Per-Server)](#68-oidc-client-authentication-per-location--per-server)
   - [6.9 Server-side and Source of Truth Authentication](#69-server-side-and-source-of-truth-authentication)
   - [6.10 NGINX Javascript (njs)](#610-nginx-javascript-njs)
   - [6.11 Stream server (Layer 4 UDP/TCP & TLS Termination)](#611-stream-server-layer-4-udptcp--tls-termination)
   - [6.12 F5 WAF for NGINX (Policies, Tags & Custom Log Profiles)](#612-f5-waf-for-nginx-policies-tags--custom-log-profiles)
   - [6.13 API Gateway (APIs.guru, Open-Meteo, Petstore v3)](#613-api-gateway-apisguru-open-meteo-petstore-v3)
   - [6.14 CRUD automation (Granular `PATCH` Operations)](#614-crud-automation-granular-patch-operations)
   - [6.15 Asynchronous configuration publish (`?async=true`)](#615-asynchronous-configuration-publish-asynctrue)
   - [6.16 GitOps autosync (`synctime > 0`)](#616-gitops-autosync-synctime--0)
7. [Automated Test Scripts, Variable Chaining & Newman CLI](#7-automated-test-scripts-variable-chaining--newman-cli)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Overview & v5.7 Architecture

The **NGINX Declarative API v5.7** translates a single high-level JSON declaration (`ConfigDeclaration`) into validated, production-ready NGINX Plus configurations, auxiliary assets (TLS certificates/keys, JWKS, njs scripts, F5 WAF policies, Redocly developer portals, Backstage catalog manifests), and deploys them to your choice of control plane:

```
+-------------------------------------------------------------------+
|                   Postman / CI-CD / GitOps Client                 |
|     POST / PATCH / GET / DELETE  http://{{ncg_host}}:5000/v5.7    |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                    NGINX Declarative API (v5.7)                   |
|  - Pydantic v5.7 Schema Validation & JSON Schema Introspection    |
|  - Incremental Declaration Patcher (CRUD by object name)          |
|  - OpenAPI 3.0 -> NGINX API Gateway & Redocly/Backstage Builder   |
|  - Background GitOps Autosync Worker & Redis Async Queue          |
+-----------------+-------------------------------+-----------------+
                  |                               |
     output.type: "nms"              output.type: "nginxone"
                  |                               |
                  v                               v
+---------------------------------+ +-------------------------------+
|   NGINX Instance Manager (NIM)  | |       NGINX One Console       |
|   Target: Instance Group        | |   Target: Config Sync Group   |
+---------------------------------+ +-------------------------------+
```

The collection is organized under `v5.7` into two mirrored top-level control-plane folders with **100% feature parity**:
- **`v5.7 / NGINX Instance Manager`** (`output.type: "nms"`)
- **`v5.7 / NGINX One Console`** (`output.type: "nginxone"`)

---

## 2. Summary of Collection Enhancements & Fixes

Compared to the upstream `contrib/postman/NGINX Declarative API.postman_collection.json`, this v5.7 collection introduces the following fixes and improvements:

1. **Fixed Upstream v5.7 Schema Validation Failures**:
   - Upgraded `NGINX One Console / API Gateway / APIs.guru / ... local OpenAPI schema` and `... + moesif` from legacy v5.6 schema paths (`declaration.http.authentication` / `declaration.http.authorization`) to v5.7 top-level `declaration.authentication` and `declaration.authorization` with location-scoped `apigateway.authentication.enforceOnPaths`.
   - Fixed `NGINX One Console / API Gateway / Petstore API / ... + WAF no log` where `log.access` and `log.error` were raw strings instead of `{"destination": "..."}` objects.
   - Fixed `NGINX One Console / API Gateway / Petstore API / ... + moesif + cache` where `output.type` was mistakenly set to `"nms"` instead of `"nginxone"`.
   - Fixed `Petstore 3 API Gateway RateLimit + JWT AuthN/AuthZ + backstage` in both control planes so `developer_portal` actually configures `"type": "backstage"` with `BackstageOptions` (`name`, `lifecycle`, `owner`, `system`) instead of duplicating `"type": "redocly"`.
   - Added `"log_profiles": []` to all `POST` declarations that define `declaration.http.policies` without custom log profiles, preventing a `TypeError: 'NoneType' object is not iterable` in `NIMNAPUtils.checkDeclarationPolicies` and `NGINXOneNAPUtils.checkDeclarationPolicies`.
2. **Full Feature Parity Between Control Planes**:
   - Added all missing folders and requests to `NGINX One Console`: `API Gateway / Open-Meteo` (3 gateway deployments + 5 client test requests), `APIs.guru` YAML + WAF deployment and XSS test, `Petstore API` Moesif + WAF + Cache deployment, `GitOps autosync / F5 WAF for NGINX and GitOps`, and `HTTPS server / TLS Offload and F5 WAF for NGINX`.
3. **Complete Coverage of v5.7 Schema Capabilities**:
   - Added **`Get v5.7 JSON Schema`** (`GET /v5.7/schema`) to `Housekeeping - common endpoints`.
   - Added **`Advanced HTTPS Reverse Proxy - Maps, Caching, JSON LogFormat & Active Health Checks`** demonstrating `.declaration.http.maps[]` (`exact`, `regex`, `iregex`), `.declaration.http.logformats[]` (`escape: "json"`), conditional access logging (`condition`), `.declaration.http.cache[]` + `.declaration.http.caching[]`, `.declaration.http.rate_limit[]`, `.declaration.http.snippet`, active `health_check`, `sticky` cookie affinity, and weighted/backup origins with `slow_start`.
   - Added **`Update F5 WAF custom security log profile`** (`PATCH`) demonstrating `.declaration.http.log_profiles[]` (`type: "app_protect"`, `format: "user-defined"`).
   - Added **`Create TLS-terminated TCP & UDP stream servers with custom log format`** demonstrating Layer 4 TCP TLS offload (`listen.tls`), `.declaration.layer4.logformats[]`, stream logging, and weighted/sticky Layer 4 upstreams.
   - Added **Steps 12, 13, and 14** to `CRUD automation` demonstrating v5.7 `DeclarationPatcher` upsert and delete-by-name operations on shared profiles (`resolvers`, `http.rate_limit`, `http.maps`, `http.logformats`, `http.cache`) followed by final state verification.
4. **Modern Postman Test Scripts & Built-In Environment Variables**:
   - Replaced deprecated `tests[...]` scripts with modern `pm.test()` / `pm.expect()` assertions across **all 180 requests** (90 per control plane: 34 `POST`, 20 `PATCH`, 11 `GET`, 2 `DELETE`, and 23 data-plane client requests).
   - Embedded **24 documented Collection Variables** (including parameterized JWT tokens and data-plane URLs) so the collection works out-of-the-box without requiring a separate environment file.

---

## 3. Quickstart Guide

### Prerequisites
- **Postman Desktop or Web** (v10+ or v11+) or **Newman CLI**.
- Running instance of the **NGINX Declarative API v5.7** container (`http://127.0.0.1:5000` by default) and Redis (for asynchronous mode).
- Access to either **NGINX Instance Manager (NIM)** or **F5 Distributed Cloud / NGINX One Console**.

### Step 1: Import the Collection
1. Open Postman and click **Import**.
2. Select `NGINX Declarative API.postman_collection.json`.
3. The collection **`NGINX Declarative API`** will appear in your workspace with all **24 Collection Variables** pre-configured.

### Step 2: Configure Your Control Plane Variables
1. Click the top-level **`NGINX Declarative API`** collection in Postman and open the **Variables** tab.
2. Update the **Current Value** column for your environment:
   - **Declarative API endpoint**: `ncg_host` (default `127.0.0.1`), `ncg_port` (default `5000`).
   - **NGINX Plus R33+ License**: `nginx_license_token` and `nginx_reporting_server`.
   - **For NGINX Instance Manager**: `nim_host`, `nim_username`, `nim_password`, `nim_instancegroup`.
   - **For NGINX One Console**: `nginxone_url`, `nginxone_token`, `nginxone_namespace`, `nginxone_configsyncgroup`.
3. Click **Save** (`Ctrl+S` / `Cmd+S`).

### Step 3: Run Your First Use Case
1. Expand `v5.7 -> NGINX Instance Manager` (or `NGINX One Console`) -> `Housekeeping - common endpoints`.
2. Send **`Get v5.7 JSON Schema`** (`GET /v5.7/schema`) to verify connectivity to the NGINX Declarative API service.
3. Open any use-case folder (e.g., `HTTPS server -> TLS Offload`) and click **Send**.
4. The post-response test script automatically validates `status.code === 0` and stores `status.configUid` into the `{{configUid}}` collection variable for subsequent `GET`, `PATCH`, and `DELETE` requests.

---

## 4. Collection & Environment Variables Reference

All variables are embedded directly in the collection's `variable` array and can also be overridden by a Postman Environment if desired.

| Variable | Default Value | Scope / Purpose |
| :--- | :--- | :--- |
| `ncg_host` | `127.0.0.1` | Hostname or IP address of the NGINX Declarative API service. |
| `ncg_port` | `5000` | TCP port exposed by the NGINX Declarative API service. |
| `ngc_api_version` | `v5.7` | Target NGINX Declarative API version prefix (`v5.7`). |
| `configUid` | *(auto-populated)* | Active configuration declaration UID captured automatically from `POST /v5.7/config` responses. |
| `submissionUid1` | *(auto-populated)* | First asynchronous submission UID captured from `POST /v5.7/config?async=true`. |
| `submissionUid2` | *(auto-populated)* | Second asynchronous submission UID captured from `PATCH /v5.7/config/{{configUid}}?async=true`. |
| `nim_host` | `https://nim.nginx.lab` | Base URL of the NGINX Instance Manager control plane (`output.nms.url`). |
| `nim_username` | `admin` | Username for NGINX Instance Manager Basic authentication (`output.nms.username`). |
| `nim_password` | `admin` | Password for NGINX Instance Manager Basic authentication (`output.nms.password`). |
| `nim_instancegroup` | `lab` | Target NGINX Instance Manager Instance Group name (`output.nms.instancegroup`). |
| `nginxone_url` | `https://console.ves.volterra.io` | Base URL of the F5 Distributed Cloud / NGINX One Console tenant (`output.nginxone.url`). |
| `nginxone_token` | `your-nginx-one-api-token` | API Token for NGINX One Console authentication (`output.nginxone.token`). |
| `nginxone_namespace` | `default` | Target NGINX One Console namespace (`output.nginxone.namespace`). |
| `nginxone_configsyncgroup` | `lab` | Target NGINX One Console Config Sync Group name (`output.nginxone.configsyncgroup`). |
| `nginx_license_token` | `your-nginx-plus-jwt-license` | NGINX Plus R33+ JWT license token (`output.license.token`). |
| `nginx_reporting_server` | `product.connect.nginx.com` | NGINX Plus usage reporting server hostname or IP (`output.license.endpoint`). |
| `github_gitops_root` | `https://raw.githubusercontent.com/f5devcentral/NGINX-Declarative-API/refs/heads/main/contrib/examples` | Base URL for external GitOps Sources of Truth (OpenAPI specs, TLS certs/keys, WAF policies). |
| `moesif_application_id` | `your-moesif-application-id` | Moesif Application ID for API analytics (`developer_portal.moesif.application_id`). |
| `apigw_url` | `https://apigw.nginx.lab` | Data-plane base URL for API Gateway client test requests. |
| `echo_app_url` | `http://echo.vm-blank.ie.ff.lan` | Data-plane base URL for the Echo test application. |
| `randomjoke_app_url` | `http://randomjoke.vm-blank.ie.ff.lan` | Data-plane base URL for the Random Joke test application. |
| `jwt_token_devops` | `eyJ0eXAiOiJKV1Qi...` | Sample HS256 JWT Bearer token with `roles: ["devops"]` claim (signed with `kid: "0001"`). |
| `jwt_token_guest` | `eyJ0eXAiOiJKV1Qi...` | Sample HS256 JWT Bearer token with `roles: ["guest"]` claim (signed with `kid: "0001"`). |
| `jwt_token_devops_guest` | `eyJ0eXAiOiJKV1Qi...` | Sample HS256 JWT Bearer token with `roles: ["devops", "guest"]` claims (signed with `kid: "0001"`). |

---

## 5. API v5.7 Endpoints Reference

| Method | Endpoint | Query Params | Success Code | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/{{ngc_api_version}}/schema` | None | `200 OK` | Returns the full Pydantic / OpenAPI JSON Schema for v5.7 `ConfigDeclaration`. |
| `POST` | `/{{ngc_api_version}}/config` | `async=true\|false` (default `false`) | `200 OK` (sync)<br>`202 Accepted` (async) | Validates, renders, and deploys a complete NGINX configuration declaration. Returns `status.configUid` (and `status.submissionUid` when asynchronous). |
| `PATCH` | `/{{ngc_api_version}}/config/{{configUid}}` | `async=true\|false` (default `false`) | `200 OK` (sync)<br>`202 Accepted` (async) | Applies an incremental CRUD patch to an existing declaration identified by `configUid`. |
| `GET` | `/{{ngc_api_version}}/config/{{configUid}}` | None | `200 OK` | Retrieves the full JSON declaration (`output` + `declaration`) currently stored for `configUid`. |
| `GET` | `/{{ngc_api_version}}/config/{{configUid}}/status` | None | `200 OK` | Retrieves the latest deployment status (`code`, `message`, `details`, `configUid`, `submissionUid`). |
| `GET` | `/{{ngc_api_version}}/config/{{configUid}}/submission/{{submissionUid}}` | None | `200 OK` | Retrieves the execution status of a specific asynchronous submission (`queued`, `running`, `succeeded`, or `failed`). |
| `DELETE` | `/{{ngc_api_version}}/config/{{configUid}}` | None | `200 OK` | Deletes the stored declaration and stops any background GitOps autosync worker bound to `configUid`. |

---

## 6. Use-Case Catalog & Folder Walkthroughs

Every folder below exists under **both** `v5.7 / NGINX Instance Manager` and `v5.7 / NGINX One Console`.

### 6.1 `Housekeeping - common endpoints`
Core lifecycle management and schema introspection requests:
1. **`Get v5.7 JSON Schema`** (`GET /v5.7/schema`) — Inspects the v5.7 JSON Schema definition.
2. **`Clean NGINX configuration`** (`POST /v5.7/config`) — Pushes an empty declaration (containing only the `output` block) to wipe all active HTTP/Stream servers from the target Instance Group or Config Sync Group.
3. **`Get declaration status`** (`GET /v5.7/config/{{configUid}}/status`) — Inspects the deployment status of the active `configUid`.
4. **`Get declaration`** (`GET /v5.7/config/{{configUid}}`) — Retrieves the stored JSON declaration for `configUid`.
5. **`Delete declaration`** (`DELETE /v5.7/config/{{configUid}}`) — Removes `configUid` from the state store and stops GitOps autosync threads.

### 6.2 `HTTPS server` (TLS Offload, WAF, Maps, Caching, Health Checks)
Demonstrates HTTPS reverse proxy deployments and advanced v5.7 HTTP traffic management:
1. **`TLS Offload`** (`POST /v5.7/config`) — Deploys an HTTP/2 TLS 1.2/1.3 reverse proxy (`www.online-boutique.lan`) fetching its TLS certificate and private key from external GitOps URLs (`{{github_gitops_root}}/{{ngc_api_version}}/testcert.crt` and `testcert.key`).
2. **`TLS Offload and F5 WAF for NGINX`** (`POST /v5.7/config`) — Extends the HTTPS reverse proxy with F5 WAF for NGINX (`ngx_http_app_protect_module`) enforcing the `production-policy` (`active_tag: "xss-blocked"`).
3. **`Advanced HTTPS Reverse Proxy - Maps, Caching, JSON LogFormat & Active Health Checks`** (`POST /v5.7/config`) — Showcases all advanced v5.7 HTTP directives:
   - **Variable Mapping (`.declaration.http.maps[]`)**: Evaluates `$http_x_env` against `exact`, `regex`, and `iregex` rules to populate `$backend_pool_tier`.
   - **Custom JSON Log Format (`.declaration.http.logformats[]`)**: Defines `json_analytics` with `escape: "json"` and conditional access logging (`condition: "$status ~ ^[2345]"`).
   - **Response Caching (`.declaration.http.cache[]` & `.declaration.http.caching[]`)**: Configures a 1 GB disk cache (`catalog_disk_cache`) and caches `GET`/`HEAD` responses on `/catalog` (`200`/`301`/`302` for `10m`, `404` for `1m`).
   - **Rate Limiting (`.declaration.http.rate_limit[]`)**: Enforces `50r/s` (`burst: 20`, HTTP `429`) on `/checkout`.
   - **Active Health Checks & Sticky Upstreams**: Enables NGINX Plus active health checks (`/healthz` every `5s`), `sticky` cookie session affinity (`boutique_srv_id`), weighted origins with `slow_start: "15s"`, and a `backup: true` failover node.

### 6.3 `ACME Protocol` (Automated TLS Certificates)
- **`TLS Offload with ACME protocol`** (`POST /v5.7/config`) — Loads `ngx_http_acme_module`, defines an ACMEv2 issuer profile in `.declaration.http.acme_issuers[]` (pointing to a Pebble/Let's Encrypt directory URL with state path and account key), and binds `listen.tls.acme_issuer` on the HTTPS server for zero-touch certificate issuance and renewal.

### 6.4 `HTTP Headers Manipulation`
Demonstrates progressive `POST` -> `PATCH` manipulation of request and response headers:
1. **`Create test echo service`** (`POST /v5.7/config`) — Deploys a baseline HTTP reverse proxy fronting `echo.free.beeceptor.com`.
2. **`Manipulate headers - server level`** (`PATCH /v5.7/config/{{configUid}}`) — Injects `X-Injected-Client-IP: $remote_addr` and `Host` toward the upstream (`headers.to_server.set`) and adds/deletes client response headers (`headers.to_client.add`, `headers.to_client.delete`) at the server level.
3. **`Manipulate headers - location level`** (`PATCH /v5.7/config/{{configUid}}`) — Moves the header manipulation rules to the `/` location scope.

### 6.5 `JWT Client Authentication`
Demonstrates client JWT validation (`declaration.authentication.client` with `type: "jwt"`) and token extraction sources:
1. **`JWT Client Authentication - local JWT key and Bearer token`** (`POST /v5.7/config`) — Defines 4 client JWT profiles and activates inline JWKS validation using standard `Authorization: Bearer` tokens.
2. **`JWT secret fetched from URL`** (`PATCH /v5.7/config/{{configUid}}`) — Switches the location to a JWT profile that fetches its JWKS remotely (`http://192.168.2.5:20080/jwks.json`, `cachetime: 5`).
3. **`JWT token in auth_token query string parameter`** (`PATCH /v5.7/config/{{configUid}}`) — Extracts the JWT from `?auth_token=...` (`token_location: "$arg_auth_token"`).
4. **`JWT token in HTTP X-Auth-Token header`** (`PATCH /v5.7/config/{{configUid}}`) — Extracts the JWT from a custom request header (`token_location: "$http_x_auth_token"`).

### 6.6 `JWT Client Authentication and Authorization` (RBAC)
- **`JWT Client Authentication and Authorization`** (`POST /v5.7/config`) — Combines `.declaration.authentication.client[]` (`type: "jwt"`, `jwt_type: "signed"`) with `.declaration.authorization[]` (`type: "jwt"`) enforcing that the JWT `roles` claim matches the regex `~(devops)`, and injects `X-Injected-JWT-Group: $jwt_claim_roles` into the client response.

### 6.7 `mTLS Client Authentication` (PKI, CRL, OCSP, Stapling)
- **`HTTPS server with mTLS, OCSP, SSL Stapling`** (`POST /v5.7/config`) — Configures mutual TLS client authentication (`listen.tls.authentication.client`) referencing `.declaration.authentication.client[]` (`type: "mtls"`) with inline Base64 PKI CA (`type: "pkica"`), Certificate Revocation List (`type: "crl"`), OCSP responder validation (`ocsp`), and OCSP stapling (`stapling`).

### 6.8 `OIDC Client Authentication` (Per-Location & Per-Server)
1. **`OIDC Client Authentication - Per Location`** (`POST /v5.7/config`) — Configures OpenID Connect authentication (`type: "oidc"` against Keycloak) on a specific location (`locations[].authentication.client`).
2. **`OIDC Client Authentication - Per Server`** (`POST /v5.7/config`) — Enforces OpenID Connect authentication across the entire virtual server (`servers[].authentication.client`).

### 6.9 `Server-side and source of truth authentication`
Demonstrates `.declaration.authentication.server[]` profiles used both when NGINX proxies to protected upstreams and when the Declarative API fetches assets from private GitOps repositories:
1. **`Bearer Token, Basic and HTTP header upstream authentication`** (`POST /v5.7/config`) — Defines `token` (`bearer` and custom `header: X-AUTH-TOKEN`) and `basic` server authentication profiles; uses `Bearer token-based authentication profile` for upstream requests and `Basic authentication profile` to authenticate the GitOps fetch of `testcert.crt`.
2. **`mTLS upstream authentication`** (`POST /v5.7/config`) — Configures NGINX to authenticate itself to the backend upstream using a client TLS certificate and key (`type: "mtls"` in `.declaration.authentication.server[]`).

### 6.10 `NGINX Javascript` (`njs`)
- **`NGINX Javascript test`** (`POST /v5.7/config`) — Loads `ngx_http_js_module` and `ngx_stream_js_module`, defines Base64-encoded `.declaration.http.njs_profiles[]` (`njs_set_variable` and `njs_set_content`), evaluates `js_set` hooks at both `http` (`$httpVarSetByNjs`) and `server` (`$serverVarSetByNjs`) contexts, and serves synthetic content on `/generatecontent` via `js_content`.

### 6.11 `Stream server` (Layer 4 UDP/TCP & TLS Termination)
1. **`Create stream server`** (`POST /v5.7/config`) — Configures a Layer 4 UDP DNS load balancer (`listen.protocol: "udp"` on port `10053`) fronting `ns1.google.com:53` and `ns2.google.com:53`.
2. **`Create TLS-terminated TCP & UDP stream servers with custom log format`** (`POST /v5.7/config`) — Configures both UDP DNS load balancing and a TLS-terminated TCP LDAPS load balancer (`listen.protocol: "tcp"`, `listen.tls` on port `10636`) with a custom stream log format (`.declaration.layer4.logformats[]`), stream access/error logs, `sticky` cookie affinity, weighted primary origins, and a backup origin.

### 6.12 `F5 WAF for NGINX` (Policies, Tags & Custom Log Profiles)
End-to-end lifecycle of F5 WAF for NGINX (`ngx_http_app_protect_module`) policies:
1. **`Create initial NGINX configuration with F5 WAF for NGINX`** (`POST /v5.7/config`) — Deploys an HTTPS server protected by `production-policy` containing two version tags (`xss-blocked` and `xss-allowed`), initially activating `active_tag: "xss-blocked"`.
2. **`Change active F5 WAF for NGINX policy`** (`PATCH /v5.7/config/{{configUid}}`) — Zero-downtime switch of `active_tag` from `"xss-blocked"` to `"xss-allowed"` via `PATCH`.
3. **`Update F5 WAF custom security log profile`** (`PATCH /v5.7/config/{{configUid}}`) — Adds a custom `user-defined` JSON security log profile (`custom_json_sec_log`) to `.declaration.http.log_profiles[]` and binds it to the location's `app_protect.log` syslog target.
4. **`Update TLS certificates`** (`PATCH /v5.7/config/{{configUid}}`) — Rotates `test_cert` and `test_key` in `.declaration.certificates[]` using inline Base64 PEM strings without touching the HTTP/WAF configuration.
5. **`Disable F5 WAF for NGINX`** (`PATCH /v5.7/config/{{configUid}}`) — Disables `app_protect` on the `/` location via `PATCH`.

### 6.13 `API Gateway` (`APIs.guru`, `Open-Meteo`, `Petstore API`)
Automatically builds complete NGINX API Gateway configurations from OpenAPI 3.0 specifications (`loc.apigateway.openapi`):
- **`APIs.guru`**:
  - Deploys the APIs.guru v2 OpenAPI specification from **inline JSON**, **external JSON URL**, **external JSON URL + Moesif analytics**, or **external YAML URL + F5 WAF (`owasp-top10`)**, complete with rate limiting, JWT AuthN/AuthZ, and Redocly developer portal.
  - Includes **`API Client test requests`** (`Metrics`, `Metrics - XSS Attack`, `Providers - no authentication`, `Providers - auth with "DevOps" token`, `Providers - auth with "Guest" token`, `Providers - auth with "DevOps" and "Guest" token`).
- **`Open-Meteo`**:
  - Deploys the Open-Meteo YAML OpenAPI specification with **Redocly**, **Redocly + Moesif**, and **Redocly + F5 WAF (`owasp-top10`)**.
  - Includes **`Open-Meteo test requests`** testing unauthenticated, XSS, DevOps-authorized, Guest-forbidden, and dual-role requests.
- **`Petstore API`**:
  - Deploys Swagger Petstore v3 across 7 progressive combinations:
    1. `RateLimit + JWT AuthN/AuthZ + redocly`
    2. `RateLimit + JWT AuthN/AuthZ + backstage` (returns generated Backstage `catalog-info.yaml` in `status.manifests[]`)
    3. `RateLimit + JWT AuthN/AuthZ + redocly + moesif`
    4. `RateLimit + JWT AuthN/AuthZ + redocly + moesif + cache`
    5. `RateLimit + JWT AuthN/AuthZ + redocly + WAF`
    6. `RateLimit + JWT AuthN/AuthZ + redocly + WAF + syslog`
    7. `RateLimit + JWT AuthN/AuthZ + redocly + moesif + WAF + cache`
  - Includes 10 **`API Client test requests`** covering legitimate requests, LFI/XSS attacks, login RBAC checks, and `POST /pet/1/uploadImage` RBAC checks.

### 6.14 `CRUD automation` (Granular `PATCH` Operations)
Demonstrates a 14-step incremental infrastructure-as-code pipeline using `PATCH /v5.7/config/{{configUid}}`:
1. **`1. Initialize configuration`** (`POST`) — Initializes an empty declaration and captures `{{configUid}}`.
2. **`2. Create upstream for echo service`** (`PATCH`) — Adds `echo_upstream` to `http.upstreams`.
3. **`3. Create server for echo service`** (`PATCH`) — Adds `Echo service` to `http.servers`.
4. **`4. Create upstream for randomjoke service`** (`PATCH`) — Adds `randomjoke_upstream` to `http.upstreams`.
5. **`5. Create server for randomjoke service`** (`PATCH`) — Adds `Random Joke service` to `http.servers`.
6. **`6. Update server for randomjoke service`** (`PATCH`) — Updates `Random Joke service` by adding `/random_joke` location and custom headers.
7. **`7. Add stream service and upstream - DNS load balancer`** (`PATCH`) — Adds `DNS Load Balancer` and `google_DNS_upstream` to `.declaration.layer4`.
8. **`8. Delete echo server`** (`PATCH`) — Deletes `Echo service` from `http.servers` by passing `{"name": "Echo service"}` only.
9. **`9. Delete echo upstream`** (`PATCH`) — Deletes `echo_upstream` from `http.upstreams` by name.
10. **`10. Delete randomjoke service`** (`PATCH`) — Deletes both `Random Joke service` and `randomjoke_upstream` in one `PATCH`.
11. **`11. Delete DNS load balancer`** (`PATCH`) — Deletes `DNS Load Balancer` and `google_DNS_upstream` from `.declaration.layer4` by name.
12. **`12. Patch shared profiles (resolvers, rate_limit, maps, logformats)`** (`PATCH`) — Upserts named objects into `resolvers`, `http.rate_limit`, `http.maps`, `http.logformats`, and `http.cache`.
13. **`13. Update resolvers & rate_limit and delete cache profile`** (`PATCH`) — Updates `Cloudflare_DNS` and `crud_dynamic_ratelimit` in place and deletes `crud_temp_cache` from `http.cache` by passing `{"name": "crud_temp_cache"}`.
14. **`14. Get final declaration`** (`GET`) — Verifies the merged declaration state.

### 6.15 `Asynchronous configuration publish` (`?async=true`)
Demonstrates non-blocking Redis-backed queued deployments:
1. **`1. Initialize configuration`** (`POST /v5.7/config`) — Synchronous initialization capturing `{{configUid}}`.
2. **`2. Asynchronously create echo and randomjoke services`** (`POST /v5.7/config?async=true`) — Returns `202 Accepted` immediately and saves `{{submissionUid1}}`.
3. **`3. Asynchronously update randomjoke service`** (`PATCH /v5.7/config/{{configUid}}?async=true`) — Queues an update on the same `{{configUid}}` and saves `{{submissionUid2}}`.
4. **`4. Get first submission status`** (`GET /v5.7/config/{{configUid}}/submission/{{submissionUid1}}`) — Polls completion of the first submission.
5. **`5. Get second submission status`** (`GET /v5.7/config/{{configUid}}/submission/{{submissionUid2}}`) — Polls completion of the second submission.
6. **`6. Test application - echo test`** & **`7. Test application - random joke`** — Data-plane verification requests.

### 6.16 `GitOps autosync` (`synctime > 0`)
Demonstrates autonomous drift detection and reconciliation (`synctime: 5` seconds):
1. **`NGINX Plus and GitOps`** (`POST /v5.7/config`) — Deploys an HTTPS reverse proxy whose certificates are fetched from `{{github_gitops_root}}` and checked for changes every 5 seconds.
2. **`F5 WAF for NGINX and GitOps`** (`POST /v5.7/config`) — Adds continuous GitOps synchronization of F5 WAF policy definitions (`nap-policy-xss-blocked.json` and `nap-policy-xss-allowed.json`).
3. **`Get declaration status`**, **`Get declaration`**, and **`Delete declaration`** — Monitors background sync status and terminates the autosync thread when finished.

---

## 7. Automated Test Scripts, Variable Chaining & Newman CLI

Every request in the collection includes an automated Postman **Test Script**:
- **Synchronous `POST /v5.7/config`**: Asserts `200 OK`, verifies `status.code === 0`, and stores `status.configUid` into `{{configUid}}`. On Backstage requests, also asserts that `status.manifests[0]` contains a valid Backstage YAML manifest.
- **Synchronous `PATCH /v5.7/config/{{configUid}}`**: Asserts `200 OK`, verifies `status.code === 0`, and confirms `status.configUid` matches `{{configUid}}`.
- **Asynchronous `POST` / `PATCH` (`?async=true`)**: Asserts `202 Accepted` and stores `status.submissionUid` into `{{submissionUid1}}` or `{{submissionUid2}}`.
- **Introspection & Lifecycle (`GET` / `DELETE`)**: Validates JSON Schema structure, deployment status payloads, stored declarations, and deletion confirmations.

### Running with Newman CLI
You can run any workflow folder from the command line using [Newman](https://learning.postman.com/docs/collections/using-newman-cli/command-line-integration-with-newman/):

```bash
# Run the complete CRUD Automation workflow on NGINX Instance Manager
newman run "NGINX Declarative API.postman_collection.json" \
  --folder "CRUD automation" \
  --env-var "ncg_host=127.0.0.1" \
  --env-var "ncg_port=5000" \
  --env-var "nim_host=https://nim.nginx.lab" \
  --env-var "nim_username=admin" \
  --env-var "nim_password=admin" \
  --env-var "nim_instancegroup=lab" \
  --insecure
```

---

## 8. Troubleshooting

| Symptom | Cause | Resolution |
| :--- | :--- | :--- |
| `404 Not Found` on `GET`/`PATCH`/`DELETE /v5.7/config/{{configUid}}` | `{{configUid}}` is empty or the NGINX Declarative API container was restarted (clearing its state store). | Run a `POST /v5.7/config` request first so the test script populates `{{configUid}}`. |
| `422 Unprocessable Entity` | Request payload does not match the v5.7 Pydantic model (`V5_7_NginxConfigDeclaration.py`). | Run `Get v5.7 JSON Schema` (`GET /v5.7/schema`) to inspect required fields and enum values. |
| `500 Internal Server Error` on WAF requests | The F5 WAF policy compiler container is unreachable (`etc/config.yaml -> f5_waf.compiler`) or `ngx_http_app_protect_module` is not installed on target NGINX instances. | Verify that the WAF compiler URL is configured in `etc/config.yaml` and target instances have F5 WAF for NGINX installed. |
| `500 Internal Server Error` on `?async=true` requests | Redis queue server is not running or unreachable. | Ensure Redis is running and configured in `etc/config.yaml` (`redis.host` / `redis.port`). |
