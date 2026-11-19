# NGINX Declarative API — Postman Collection & Environment Guide

This directory contains the **Postman Collection v2.1** (`NGINX Declarative API.postman_collection.json`) with built-in **Collection Variables** for demonstrating, testing, and automating every capability of the **[NGINX Declarative API](https://github.com/f5devcentral/NGINX-Declarative-API)** across **`v5.5`**, **`v5.6`**, and **`v5.7`**.

---

## Table of Contents

1. [Overview & Architecture](#1-overview--architecture)
2. [Collection Layout & Version Summary](#2-collection-layout--version-summary)
3. [Quickstart Guide](#3-quickstart-guide)
4. [Collection Variables Reference](#4-collection-variables-reference)
5. [API v5.7 Endpoints Reference](#5-api-v57-endpoints-reference)
6. [v5.7 Use-Case Catalog & Folder Walkthroughs](#6-v57-use-case-catalog--folder-walkthroughs)
   - [6.1 Housekeeping - common endpoints](#61-housekeeping---common-endpoints)
   - [6.2 HTTPS server](#62-https-server)
   - [6.3 ACME Protocol](#63-acme-protocol)
   - [6.4 HTTP Headers Manipulation](#64-http-headers-manipulation)
   - [6.5 JWT Client Authentication](#65-jwt-client-authentication)
   - [6.6 JWT Client Authentication and Authorization](#66-jwt-client-authentication-and-authorization)
   - [6.7 mTLS Client Authentication](#67-mtls-client-authentication)
   - [6.8 OIDC Client Authentication](#68-oidc-client-authentication)
   - [6.9 Server-side and source of truth authentication](#69-server-side-and-source-of-truth-authentication)
   - [6.10 NGINX Javascript](#610-nginx-javascript)
   - [6.11 Stream server](#611-stream-server)
   - [6.12 F5 WAF for NGINX](#612-f5-waf-for-nginx)
   - [6.13 API Gateway](#613-api-gateway)
   - [6.14 CRUD automation](#614-crud-automation)
   - [6.15 Asynchronous configuration publish](#615-asynchronous-configuration-publish)
   - [6.16 GitOps autosync](#616-gitops-autosync)
7. [Automated Test Scripts, Variable Chaining & Newman CLI](#7-automated-test-scripts-variable-chaining--newman-cli)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Overview & Architecture

The **NGINX Declarative API** translates a single high-level JSON declaration (`output` + `declaration`) into validated NGINX Plus configurations and auxiliary assets (TLS certificates/keys, JWKS, njs scripts, F5 WAF policies, Redocly developer portals, Backstage catalog manifests), and deploys them to your chosen control plane:

```
+-------------------------------------------------------------------+
|                   Postman / CI-CD / GitOps Client                 |
|  POST / PATCH / GET / DELETE  http://{{ncg_host}}:5000/v5.7       |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                    NGINX Declarative API (v5.7)                   |
|  - Pydantic v5.7 Schema Validation & JSON Schema Introspection    |
|  - Incremental Declaration Patcher (CRUD by object name)          |
|  - OpenAPI 3.0 -> NGINX API Gateway & Redocly/Backstage Builder   |
|  - Background GitOps Autosync Worker & Async Submission Queue     |
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

---

## 2. Collection Layout & Version Summary

The collection (`NGINX Declarative API.postman_collection.json`) contains **127 folders** and **449 requests** (`195 POST`, `140 GET`, `102 PATCH`, `12 DELETE`) organized into three top-level API version folders:

| Version Folder | Subfolders | Requests | Control-Plane Branches & Coverage |
| :--- | :---: | :---: | :--- |
| **`v5.5`** | 37 | 124 | `NGINX Instance Manager` (65 requests across 16 feature folders, including `NGINX App Protect WAF` and WAF variants) and `NGINX One Console` (59 requests across 15 feature folders). |
| **`v5.6`** | 41 | 141 | `NGINX Instance Manager` (74 requests across 16 feature folders, adding `F5 WAF for NGINX` and `API Gateway / APIs.guru`) and `NGINX One Console` (67 requests across 15 feature folders). |
| **`v5.7`** *(default)* | 46 | 184 | **100% feature parity** between `NGINX Instance Manager` (`output.type: "nms"`) and `NGINX One Console` (`output.type: "nginxone"`): **92 requests per control plane** (**71** control-plane API calls: `38 POST`, `11 GET`, `20 PATCH`, `2 DELETE`; plus **21** data-plane client test requests: `18 GET`, `3 POST`), all with `pm.test()` scripts. |

### Key Highlights in `v5.7`

- **100% Control-Plane Parity**: Every feature folder and request in `v5.7 / NGINX Instance Manager` is mirrored identically in `v5.7 / NGINX One Console`.
- **Full OpenAPI 3.0 `servers` Support (`API Gateway / Open-Meteo`)**: Showcases root `.servers[]` multiple upstreams, per-path `.paths.<NAME>.servers[]` upstreams, and OpenAPI server template `variables` (`default`, `enum`, `description`) in both root and path-level server definitions.
- **Complete `v5.7` Feature Coverage**:
  - `GET /{{ngc_api_version}}/schema` introspection in `Housekeeping - common endpoints`.
  - **Advanced HTTPS Reverse Proxy**: `.declaration.http.maps[]`, JSON `.declaration.http.logformats[]`, conditional access logging, `.declaration.http.cache[]` + `.declaration.http.caching[]`, `.declaration.http.rate_limit[]`, `.declaration.http.snippet`, active `health_check`, `sticky` cookie affinity, and weighted/backup origins with `slow_start`.
  - **F5 WAF Custom Security Log Profiles**: `PATCH` support for `.declaration.http.log_profiles[]` (`type: "app_protect"`, `format: "user-defined"`).
  - **Layer 4 Stream TLS & Telemetry**: `listen.tls` on TCP stream servers, `.declaration.layer4.logformats[]`, weighted primary origins, and backup failover origins.
  - **Extended CRUD Automation**: Incremental `PATCH` create/update/delete-by-name across HTTP, Layer 4, `resolvers`, `http.rate_limit`, `http.cache`, `http.maps`, and `http.logformats`.
- **24 Built-In Collection Variables**: Parameterized endpoints, control-plane credentials, GitOps URLs, and sample JWT tokens work out-of-the-box without requiring a separate environment file.

> [!NOTE]
> All control-plane URLs across `v5.5`, `v5.6`, and `v5.7` use `{{ngc_api_version}}` (default: `v5.7`). Update `ngc_api_version` in Collection Variables if you run requests under `v5.5` or `v5.6`.

---

## 3. Quickstart Guide

### Prerequisites
- **Postman Desktop or Web** (or **Newman CLI**).
- Running instance of the **NGINX Declarative API** (`http://127.0.0.1:5000` by default) and Redis (required for asynchronous submissions).
- Access to **NGINX Instance Manager (NIM)** or **F5 Distributed Cloud / NGINX One Console**.

### Step 1: Import the Collection
1. Open Postman and click **Import**.
2. Select `NGINX Declarative API.postman_collection.json`.
3. The collection **`NGINX Declarative API`** appears with all **24 Collection Variables** pre-configured.

### Step 2: Configure Your Control Plane Variables
1. Select the top-level **`NGINX Declarative API`** collection and open the **Variables** tab.
2. Update the **Current Value** column for your environment:
   - **Declarative API endpoint**: `ncg_host` (default `127.0.0.1`), `ncg_port` (default `5000`), `ngc_api_version` (default `v5.7`).
   - **NGINX Plus R33+ License**: `nginx_license_token` and `nginx_reporting_server`.
   - **For NGINX Instance Manager**: `nim_host`, `nim_username`, `nim_password`, `nim_instancegroup`.
   - **For NGINX One Console**: `nginxone_url`, `nginxone_token`, `nginxone_namespace`, `nginxone_configsyncgroup`.
3. Save the collection (`Ctrl+S` / `Cmd+S`).

### Step 3: Run Your First Use Case
1. Expand `v5.7 -> NGINX Instance Manager` (or `NGINX One Console`) -> `Housekeeping - common endpoints`.
2. Send **`Get v5.7 JSON Schema`** (`GET /{{ngc_api_version}}/schema`) to verify connectivity.
3. Open any use-case folder (for example, `HTTPS server -> TLS Offload`) and click **Send**.
4. The post-response test script validates the `200 OK` response and saves the returned `configUid` into `{{configUid}}` for subsequent `GET`, `PATCH`, and `DELETE` requests.

---

## 4. Collection Variables Reference

All 24 variables are embedded in the collection's `variable` array and can also be overridden by a Postman Environment or Newman `--env-var` flags.

| Variable | Default Value | Description / Usage |
| :--- | :--- | :--- |
| `ncg_host` | `127.0.0.1` | Hostname or IP address of the NGINX Declarative API service. |
| `ncg_port` | `5000` | TCP port exposed by the NGINX Declarative API service. |
| `ngc_api_version` | `v5.7` | Target NGINX Declarative API version prefix (`v5.7`). |
| `configUid` | *(auto-populated)* | Active configuration declaration UID, captured automatically by synchronous `POST` / `PATCH` test scripts. |
| `submissionUid1` | *(auto-populated)* | First asynchronous submission UID, captured by `2a. Publish application - echo test`. |
| `submissionUid2` | *(auto-populated)* | Second asynchronous submission UID, captured by `3a. Publish application - random joke`. |
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
| `github_gitops_root` | `https://raw.githubusercontent.com/f5devcentral/NGINX-Declarative-API/refs/heads/main/contrib/gitops-examples` | Base HTTP(S) URL for external GitOps Sources of Truth (OpenAPI specs, TLS certs/keys, WAF policies, JWKS). |
| `moesif_application_id` | `your-moesif-application-id` | Moesif Application ID for API analytics (`apigateway.visibility[].moesif.application_id`). |
| `apigw_url` | `https://apigw.nginx.lab` | Defined for API Gateway data-plane base URL reference (existing API Gateway test requests target `https://apigw.nginx.lab/...` directly). |
| `echo_app_url` | `http://echo.vm-blank.ie.ff.lan` | Defined for Echo app data-plane reference (`v5.5`/`v5.6` async test requests target `http://echo.vm-blank.ie.ff.lan` directly). |
| `randomjoke_app_url` | `http://randomjoke.vm-blank.ie.ff.lan` | Defined for Random Joke data-plane reference (`v5.5`/`v5.6` async test requests target `http://randomjoke.vm-blank.ie.ff.lan/random_joke` directly). |
| `jwt_token_devops` | `eyJ0eXAiOiJKV1Qi...` | Sample HS256 JWT Bearer token with `roles: ["devops"]` claim (`kid: "0001"`). |
| `jwt_token_guest` | `eyJ0eXAiOiJKV1Qi...` | Sample HS256 JWT Bearer token with `roles: ["guest"]` claim (`kid: "0001"`). |
| `jwt_token_devops_guest` | `eyJ0eXAiOiJKV1Qi...` | Sample HS256 JWT Bearer token with dual `roles: ["devops", "guest"]` claims (`kid: "0001"`). |

---

## 5. API v5.7 Endpoints Reference

| Method | Endpoint | Asynchronous Mode | Success Code | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/{{ngc_api_version}}/schema` | N/A | `200 OK` | Retrieves the OpenAPI / Pydantic JSON Schema for configuration declarations. |
| `POST` | `/{{ngc_api_version}}/config` | `output.synchronous: true\|false` | `200 OK` (sync)<br>`202 Accepted` (async) | Validates, renders, and deploys a full NGINX configuration declaration, returning `configUid`. |
| `PATCH` | `/{{ngc_api_version}}/config/{{configUid}}` | `output.synchronous: true\|false` | `200 OK` (sync)<br>`202 Accepted` (async) | Applies incremental CRUD updates to an active declaration identified by `configUid`. Returns `submissionUid` when `output.synchronous` is `false`. |
| `GET` | `/{{ngc_api_version}}/config/{{configUid}}` | N/A | `200 OK` | Retrieves the stored JSON declaration (`output` and `declaration`) for `configUid`. |
| `GET` | `/{{ngc_api_version}}/config/{{configUid}}/status` | N/A | `200 OK` | Retrieves the latest deployment status of a declaration. |
| `GET` | `/{{ngc_api_version}}/config/{{configUid}}/submission/{{submissionUid}}` | N/A | `200 OK` | Retrieves the status of a specific asynchronous submission (`{{submissionUid1}}` / `{{submissionUid2}}`). |
| `DELETE` | `/{{ngc_api_version}}/config/{{configUid}}` | N/A | `200 OK` | Deletes the stored declaration and stops any background GitOps autosync worker. |

---

## 6. v5.7 Use-Case Catalog & Folder Walkthroughs

All 16 folders below exist identically under both **`v5.7 / NGINX Instance Manager`** and **`v5.7 / NGINX One Console`** (listed in folder order as organized in the collection).

### 6.1 `Housekeeping - common endpoints`
Core lifecycle management and schema introspection (**6 requests**):
1. **`Get v5.7 JSON Schema`** (`GET /{{ngc_api_version}}/schema`) — Retrieves the v5.7 JSON Schema (`properties.output`, `properties.declaration`).
2. **`Clean NGINX configuration`** (`POST /{{ngc_api_version}}/config`) — Pushes an empty declaration (only the `output` block) to clear active configurations.
3. **`TLS Offload and F5 WAF for NGINX`** (`POST /{{ngc_api_version}}/config`) — Deploys a baseline HTTPS server protected by F5 WAF (`production-policy` with `"log_profiles": []`) for quick status/retrieval testing.
4. **`Get declaration status`** (`GET /{{ngc_api_version}}/config/{{configUid}}/status`) — Queries the deployment status of `{{configUid}}`.
5. **`Get declaration`** (`GET /{{ngc_api_version}}/config/{{configUid}}`) — Retrieves the stored declaration JSON (`output` and `declaration`).
6. **`Delete declaration`** (`DELETE /{{ngc_api_version}}/config/{{configUid}}`) — Deletes `{{configUid}}` and stops any background GitOps autosync thread.

### 6.2 `HTTPS server`
HTTPS reverse proxy deployments with TLS offload, WAF, and advanced traffic management (**3 requests**):
1. **`TLS Offload and F5 WAF for NGINX`** (`POST`) — Deploys an HTTP/2 TLS 1.2/1.3 reverse proxy (`www.online-boutique.lan`) fetching certificates from `{{github_gitops_root}}/{{ngc_api_version}}/` and enabling F5 WAF (`ngx_http_app_protect_module`, `production-policy`).
2. **`TLS Offload`** (`POST`) — Minimal HTTP/2 TLS 1.2/1.3 reverse proxy fetching `testcert.crt` and `testcert.key` from GitOps URLs.
3. **`Advanced HTTPS Reverse Proxy - Maps, Caching, JSON LogFormat & Active Health Checks`** (`POST`) — Combines advanced HTTP directives for `www.online-boutique.lan` and `shop.online-boutique.lan`:
   - **Maps (`.declaration.http.maps[]`)**: Evaluates `$http_x_env` (`exact`, `regex`, `iregex`) into `$backend_pool_tier` and injects `X-Routed-Tier` and `X-Cache-Status` response headers.
   - **JSON Log Format (`.declaration.http.logformats[]`)**: Defines `json_analytics` (`escape: "json"`) with conditional logging (`condition: "$status"`).
   - **Caching (`.declaration.http.cache[]` & `.declaration.http.caching[]`)**: Configures disk cache zone `catalog_disk_cache` (`1g` max size) and caches `/catalog` (`200`/`301`/`302` for `10m`, `404` for `1m`).
   - **Rate Limiting (`.declaration.http.rate_limit[]`)**: Enforces `50r/s` (`burst: 20`, HTTP `429`) on `/checkout`.
   - **Active Health Checks & Sticky Upstreams**: Configures `health_check` (`/healthz` every `5s`), `sticky` cookie affinity (`boutique_srv_id`), weighted origins with `slow_start: "15s"`, and a `backup: true` node on `upstream_boutique_ha`.

### 6.3 `ACME Protocol`
- **`TLS Offload with ACME protocol`** (`POST`) — Loads `ngx_http_acme_module`, configures `.declaration.http.acme_issuers[]` (`ACME example issuer` with RSA-2048 key and trusted CA certificate), and references `listen.tls.acme_issuer` on `www.online-boutique.lan`.

### 6.4 `HTTP Headers Manipulation`
Progressive `POST` -> `PATCH` HTTP header rewriting (**3 requests**):
1. **`Create test echo service`** (`POST`) — Deploys baseline HTTP server `Test echo app` (`echo.vm-test.ie.ff.lan`).
2. **`Manipulate headers - server level`** (`PATCH`) — Sets upstream request headers (`X-Injected-Client-IP`, `X-Injected-Echo-Test-Version`, `Host`), removes `User-Agent`, and adds/deletes/replaces client response headers (`X-Injected-Response-Status`, `vary`, `Server`) at the server level.
3. **`Manipulate headers - location level`** (`PATCH`) — Moves the `to_server` and `to_client` header rules down to the `/` location scope.

### 6.5 `JWT Client Authentication`
Client-side JWT verification (`.declaration.authentication.client[]` with `type: "jwt"`) across token extraction mechanisms (**4 requests**):
1. **`JWT Client Authentication - local JWT key and Bearer token`** (`POST`) — Defines 4 JWT client profiles and activates inline JWKS validation using standard `Authorization: Bearer` tokens.
2. **`JWT secret fetched from URL`** (`PATCH`) — Switches the location profile to fetch its JWKS remotely (`http://192.168.2.5:20080/jwks.json`, `cachetime: 5`).
3. **`JWT token in auth_token query string parameter`** (`PATCH`) — Switches to query-parameter token extraction (`token_location: "$arg_auth_token"`).
4. **`JWT token in HTTP X-Auth-Token header`** (`PATCH`) — Switches to custom header extraction (`token_location: "$http_x_auth_token"`).

### 6.6 `JWT Client Authentication and Authorization`
- **`JWT Client Authentication and Authorization`** (`POST`) — Combines `.declaration.authentication.client[]` (`type: "jwt"`) with `.declaration.authorization[]` (`type: "jwt"`) requiring the `roles` claim to match `~(devops)` on `JWT AuthN and AuthZ test server` (`test.nginx.lab`).

### 6.7 `mTLS Client Authentication`
- **`HTTPS server with mTLS, OCSP, SSL Stapling`** (`POST`) — Enables mutual TLS (`listen.tls.authentication.client`) on `vm-blank.ff.lan` using inline Base64 client certificates, trusted CA certificates, OCSP validation (`ocsp`), and SSL stapling (`stapling`).

### 6.8 `OIDC Client Authentication`
OpenID Connect Relying Party authentication (`type: "oidc"` against Keycloak) (**2 requests**):
1. **`OIDC Client Authentication - Per Location`** (`POST`) — Attaches the `Keycloak authentication` profile to `locations[].authentication.client`.
2. **`OIDC Client Authentication - Per Server`** (`POST`) — Enforces `Keycloak authentication` across the entire server (`servers[].authentication.client`).

### 6.9 `Server-side and source of truth authentication`
Upstream and GitOps Source-of-Truth authentication using `.declaration.authentication.server[]` (**2 requests**):
1. **`Bearer Token, Basic and HTTP header upstream authentication`** (`POST`) — Defines three `type: "token"` profiles (`bearer`, custom `header` `X-AUTH-TOKEN`, and `basic`), authenticating upstream requests with Bearer token and fetching `testcert.crt` from GitOps using the Basic auth profile.
2. **`mTLS upstream authentication`** (`POST`) — Defines a `type: "mtls"` server profile with `client_cert` / `client_key` to authenticate NGINX Plus toward the upstream backend.

### 6.10 `NGINX Javascript`
- **`NGINX Javascript test`** (`POST`) — Loads `ngx_http_js_module` and `ngx_stream_js_module`, defines `.declaration.http.njs_profiles[]` (`njs_set_variable` and `njs_set_content`), evaluates `js_set` (`$httpVarSetByNjs`) at the HTTP level, and binds `js_content` (`njsSetContent`) to a location on `njs-test.vm-test.ie.ff.lan`.

### 6.11 `Stream server`
Layer 4 TCP and UDP load balancing (`.declaration.layer4`) (**2 requests**):
1. **`Create stream server`** (`POST`) — Configures a UDP DNS load balancer (`DNS Load Balancer` listening on port `10053`, `protocol: "udp"`) fronting `ns1.google.com:53` and `ns2.google.com:53`.
2. **`Create TLS-terminated TCP & UDP stream servers with custom log format`** (`POST`) — Defines a stream log format (`stream_telemetry` in `.declaration.layer4.logformats[]`), a weighted UDP DNS load balancer (`0.0.0.0:10053`), and a TLS-terminated TCP LDAPS load balancer (`0.0.0.0:10636`, `listen.tls`) with weighted primary and `backup: true` origins.

### 6.12 `F5 WAF for NGINX`
End-to-end F5 WAF for NGINX (`ngx_http_app_protect_module`) policy and logging lifecycle (**5 requests**):
1. **`Create initial NGINX configuration with F5 WAF for NGINX`** (`POST`) — Deploys `production-policy` (with tags `xss-blocked` and `xss-allowed`, `active_tag: "xss-blocked"`) alongside `custom_waf_log_profile`.
2. **`Change active F5 WAF for NGINX policy`** (`PATCH`) — Switches `active_tag` from `"xss-blocked"` to `"xss-allowed"`.
3. **`Update F5 WAF custom security log profile`** (`PATCH`) — Defines `custom_json_sec_log` (`format: "user-defined"`, JSON format string) in `.declaration.http.log_profiles[]` and binds it to the `/` location's `app_protect.log` syslog target.
4. **`Update TLS certificates`** (`PATCH`) — Updates `test_cert` and `test_key` in `.declaration.certificates[]` using inline Base64 PEM strings.
5. **`Disable F5 WAF for NGINX`** (`PATCH`) — Disables `app_protect` (`enabled: false`) on the `/` location.

### 6.13 `API Gateway`
Generates complete NGINX API Gateway configurations from OpenAPI 3.0 specifications (`apigateway.openapi_schema.content`) across three API catalogs (**16 deployment `POST` requests + 21 data-plane client test requests per control plane**):

- **`APIs.guru`** (`4` deployment requests + `6` test requests in `API Client test requests`):
  - Deployment variants using `https://api.apis.guru/v2/openapi.yaml` (or an inline Base64-encoded schema in **`local OpenAPI schema`**):
    1. `APIGuru API Gateway RateLimit + JWT AuthN/AuthZ + redocly - YAML OpenAPI schema`
    2. `APIGuru API Gateway RateLimit + JWT AuthN/AuthZ + redocly + WAF - YAML OpenAPI schema`
    3. `APIGuru API Gateway RateLimit + JWT AuthN/AuthZ + redocly - local OpenAPI schema`
    4. `APIGuru API Gateway RateLimit + JWT AuthN/AuthZ + redocly + moesif`
  - Client tests (`GET`): `Metrics`, `Metrics - XSS Attack`, and `Providers` (no auth -> `401`, DevOps token -> `200`/`429`, Guest token -> `403`, DevOps + Guest token -> `200`/`429`).

- **`Open-Meteo`** (`6` deployment requests + `5` test requests in `Open-Meteo test requests`):
  - Baseline Open-Meteo YAML (`https://raw.githubusercontent.com/open-meteo/open-meteo/refs/heads/main/openapi/forecast.yml`) variants:
    1. `Open-Meteo API Gateway RateLimit + JWT AuthN/AuthZ + redocly - YAML OpenAPI schema`
    2. `Open-Meteo API Gateway RateLimit + JWT AuthN/AuthZ + redocly + WAF - YAML OpenAPI schema`
    3. `Open-Meteo API Gateway RateLimit + JWT AuthN/AuthZ + redocly + moesif`
  - **OpenAPI 3.0 `servers` Specification Showcase** (inline Base64 YAML schemas):
    4. `OpenAPI Servers - Root Multiple Servers (.servers[])` — Defines multiple root `.servers[].url` targets (`https://api.open-meteo.com`, `https://customer-api.open-meteo.com`) to build a multi-server NGINX upstream.
    5. `OpenAPI Servers - Per-Path Upstream Servers (.paths.<NAME>.servers[])` — Routes `/v1/status` via the default `api_gateway.server_url` upstream while `/v1/forecast` defines its own `.paths./v1/forecast.servers[]` upstream group.
    6. `OpenAPI Servers - Server Variables (.servers[].variables & .paths.<NAME>.servers[].variables)` — Demonstrates OpenAPI template variables (`{username}`, `{port}`, `{basePath}`, `{sub}`, `{backup_sub}`) with `default`, `enum`, and `description` in both root `.servers[]` and path `.paths./v1/forecast.servers[]`.
  - Client tests (`GET`): Forecast no-auth (`401`), XSS attack (`200`/`400`/`403`), DevOps token (`200`/`429`), Guest token (`403`), and DevOps + Guest token (`200`/`429`).

- **`Petstore API`** (`6` deployment requests + `10` test requests in `API Client test requests`):
  - Swagger Petstore v3 (`https://petstore3.swagger.io/api/v3/openapi.json`) deployment combinations:
    1. `Petstore 3 API Gateway RateLimit + JWT AuthN/AuthZ + redocly`
    2. `Petstore 3 API Gateway RateLimit + JWT AuthN/AuthZ + backstage` *(configures `developer_portal.type: "backstage"` with `name`, `lifecycle`, `owner`, and `system`)*
    3. `Petstore 3 API Gateway RateLimit + JWT AuthN/AuthZ + redocly + moesif`
    4. `Petstore 3 API Gateway RateLimit + JWT AuthN/AuthZ + redocly + WAF`
    5. `Petstore 3 API Gateway RateLimit + JWT AuthN/AuthZ + redocly + WAF + syslog` *(binds `secops_dashboard` log profile and syslog targets)*
    6. `Petstore 3 API Gateway RateLimit + JWT AuthN/AuthZ + redocly + moesif + WAF + cache` *(adds `.declaration.http.cache[]` `"10m cache"`)*
  - Client tests (`7 GET`, `3 POST`): Store inventory (legitimate, `/etc/passwd` query injection, XSS attack), `/user/login` RBAC matrix (no auth, DevOps, Guest, DevOps+Guest), and `POST /pet/1/uploadImage` binary upload RBAC checks.

### 6.14 `CRUD automation`
Incremental create, update, and delete-by-name workflow via `PATCH /{{ngc_api_version}}/config/{{configUid}}` (**11 requests**):
1. **`Create initial NGINX configuration`** (`POST`) — Creates `HTTP test application` and `test_upstream`.
2. **`Update HTTP upstream`** (`PATCH`) — Scales `test_upstream` to 5 origin servers (`10.0.0.1`–`10.0.0.5`).
3. **`Modify and add HTTP upstream`** (`PATCH`) — Modifies `test_upstream` and adds `test_upstream_added`.
4. **`Add stream server and upstream`** (`PATCH`) — Adds Layer 4 `TCP_15432_service` and `TCP_15432_upstream`.
5. **`Remove HTTP server and upstream`** (`PATCH`) — Deletes `HTTP test application` and `test_upstream_added` by name.
6. **`Add Stream server and upstream`** (`PATCH`) — Adds Layer 4 `TCP_10053_service` and `TCP_10053_upstream`.
7. **`Remove stream server and upstream #1`** (`PATCH`) — Deletes `TCP_10053_service` and `TCP_10053_upstream` by name.
8. **`Remove stream server and upstream #2`** (`PATCH`) — Deletes `TCP_15432_service` and `TCP_15432_upstream` by name.
9. **`Patch shared profiles (resolvers, rate_limit, cache, maps, logformats)`** (`PATCH`) — Upserts `Cloudflare_DNS` (`resolvers`), `crud_dynamic_ratelimit` (`http.rate_limit`), `crud_disk_cache` (`http.cache`), a map rule (`http.maps`), and `crud_compact_log` (`http.logformats`).
10. **`Update resolvers & rate_limit and delete cache profile`** (`PATCH`) — Updates `Cloudflare_DNS` and `crud_dynamic_ratelimit` in place and deletes `crud_disk_cache` by passing `{"name": "crud_disk_cache"}`.
11. **`Get final declaration`** (`GET`) — Retrieves and verifies the merged declaration (`output` + `declaration`).

### 6.15 `Asynchronous configuration publish`
Non-blocking deployments using `output.synchronous: false` and submission polling (**8 requests**):
1. **`1. Initialize configuration`** (`POST /{{ngc_api_version}}/config`) — Synchronous baseline initialization, capturing `{{configUid}}`.
2. **`1a. Get declaration status`** (`GET /{{ngc_api_version}}/config/{{configUid}}/status`) — Checks initial status.
3. **`1b. Get declaration`** (`GET /{{ngc_api_version}}/config/{{configUid}}`) — Reads the initial declaration.
4. **`2a. Publish application - echo test`** (`PATCH /{{ngc_api_version}}/config/{{configUid}}` with `output.synchronous: false`) — Queues `Test echo app`, asserts `202 Accepted`, and stores `submissionUid` in `{{submissionUid1}}`.
5. **`2b. Get asynchronous submission status - echo test`** (`GET /{{ngc_api_version}}/config/{{configUid}}/submission/{{submissionUid1}}`) — Checks status of the first submission.
6. **`3a. Publish application - random joke`** (`PATCH /{{ngc_api_version}}/config/{{configUid}}` with `output.synchronous: false`) — Queues `Random joke application`, asserts `202 Accepted`, and stores `submissionUid` in `{{submissionUid2}}`.
7. **`3b. Get asynchronous submission status - random joke`** (`GET /{{ngc_api_version}}/config/{{configUid}}/submission/{{submissionUid2}}`) — Checks status of the second submission.
8. **`4. Get declaration`** (`GET /{{ngc_api_version}}/config/{{configUid}}`) — Retrieves the final merged declaration.

### 6.16 `GitOps autosync`
Continuous polling of external Sources of Truth (`output.nms.synctime: 5` / `output.nginxone.synctime: 5`) (**5 requests**):
1. **`NGINX Plus and GitOps`** (`POST`) — Deploys `Online boutique HTTPS` with certificates polled from `{{github_gitops_root}}` every 5 seconds.
2. **`F5 WAF for NGINX and GitOps`** (`POST`) — Enables continuous GitOps polling for both TLS certificates and `production-policy` F5 WAF JSON policies.
3. **`Get declaration status`** (`GET /{{ngc_api_version}}/config/{{configUid}}/status`) — Inspects sync status.
4. **`Get declaration`** (`GET /{{ngc_api_version}}/config/{{configUid}}`) — Reads the current declaration.
5. **`Delete declaration`** (`DELETE /{{ngc_api_version}}/config/{{configUid}}`) — Removes `{{configUid}}` and stops the background autosync worker.

---

## 7. Automated Test Scripts, Variable Chaining & Newman CLI

Every request under `v5.7` includes a `pm.test()` / `pm.expect()` post-response script:

- **Synchronous `POST` / `PATCH`**: Asserts `200 OK`, checks that `configUid` is a non-empty string, and updates `pm.collectionVariables.set("configUid", respData.configUid)`.
- **Asynchronous `PATCH` (`output.synchronous: false`)**: Asserts `202 Accepted`, verifies a non-empty `submissionUid`, and saves it to `submissionUid1` or `submissionUid2`.
- **`GET /schema`**: Asserts `200 OK` and verifies `properties.output` and `properties.declaration`.
- **`GET /config/{{configUid}}` & Status / Submission Endpoints**: Asserts `200 OK` (and `output` + `declaration` keys in `Get final declaration` and `Housekeeping / Get declaration`).
- **`DELETE /config/{{configUid}}`**: Asserts `200 OK` (and `status.code === 200` in `Housekeeping / Delete declaration`).
- **Data-Plane Client Test Requests**:
  - Authorized requests: status in `[200, 201, 429]`.
  - Unauthenticated requests: `401 Unauthorized`.
  - Forbidden role (`Guest` token): `403 Forbidden`.
  - WAF XSS / LFI probes: status in `[200, 400, 403]`.

### Running with Newman CLI

You can execute workflows from the command line using [Newman](https://learning.postman.com/docs/collections/using-newman-cli/command-line-integration-with-newman/):

```bash
# Run the complete v5.7 NGINX Instance Manager suite (all 16 folders)
newman run "NGINX Declarative API.postman_collection.json" \
  --folder "v5.7" \
  --env-var "ncg_host=127.0.0.1" \
  --env-var "ncg_port=5000" \
  --env-var "ngc_api_version=v5.7" \
  --env-var "nim_host=https://nim.nginx.lab" \
  --env-var "nim_username=admin" \
  --env-var "nim_password=admin" \
  --env-var "nim_instancegroup=lab" \
  --insecure
```

> [!TIP]
> Because `v5.5`, `v5.6`, and `v5.7` all contain identically named subfolders (such as `CRUD automation` under both control planes), targeting a leaf folder by name in Newman runs the first matching folder; use uniquely targeted collection exports or Postman Collection Runner when running a single subfolder under a specific version and control plane.

---

## 8. Troubleshooting

| Symptom | Cause | Resolution |
| :--- | :--- | :--- |
| `404 Not Found` on `GET`/`PATCH`/`DELETE /v5.7/config/{{configUid}}` | `{{configUid}}` is empty or the Declarative API service restarted (clearing in-memory/local state). | Run a synchronous `POST /{{ngc_api_version}}/config` request first so its test script populates `{{configUid}}`. |
| `422 Unprocessable Entity` | Request payload does not satisfy the `v5.7` Pydantic schema (`V5_7_NginxConfigDeclaration.py`). | Run `Get v5.7 JSON Schema` (`GET /{{ngc_api_version}}/schema`) to verify required fields and valid enum values. |
| `500 Internal Server Error` on WAF requests | The F5 WAF policy compiler is unreachable or `ngx_http_app_protect_module` is unavailable on target instances. | Verify the WAF compiler configuration in `etc/config.yaml` and confirm F5 WAF for NGINX is installed on the target data plane. |
| `500 Internal Server Error` on `output.synchronous: false` requests | Redis queue backend is stopped or unreachable. | Ensure Redis is running and properly configured in `etc/config.yaml`. |
