# Supported Features

NGINX Declarative API translates JSON/YAML declarations—and Swagger/OpenAPI specifications—into staged NGINX Plus configurations for **NGINX Instance Manager** and **NGINX One Console** across API versions `v5.5`, `v5.6`, and `v5.7`.

> **Legend:** `✅` Supported · `—` Not supported in this API version

## Table of Contents

- [Control Plane Support](#control-plane-support)
- [NGINX HTTP and Stream Servers](#nginx-http-and-stream-servers)
  - [Core Capabilities](#core-capabilities)
  - [HTTP Location Match Modifiers](#http-location-match-modifiers)
  - [HTTP Headers Manipulation](#http-headers-manipulation)
  - [Maps](#maps)
- [NGINX API Gateway](#nginx-api-gateway)
  - [API Gateway Capabilities](#api-gateway-capabilities)
  - [Request Body Schema Validation](#request-body-schema-validation)
  - [OpenAPI Specification Version Support](#openapi-specification-version-support)
  - [Configuration Reference](#configuration-reference)
  - [Developer Portal and API Visibility](#developer-portal-and-api-visibility)
- [Security and Authentication](#security-and-authentication)
  - [TLS and ACME Protocol](#tls-and-acme-protocol)
  - [Client Authentication](#client-authentication)
  - [Client Authorization](#client-authorization)
  - [Upstream and Source of Truth Authentication](#upstream-and-source-of-truth-authentication)
- [Observability, DNS, and Scripting](#observability-dns-and-scripting)
  - [HTTP Access and Error Logging](#http-access-and-error-logging)
  - [Access Logging Formats](#access-logging-formats)
  - [DNS Resolvers](#dns-resolvers)
  - [NGINX JavaScript](#nginx-javascript)

---

## Control Plane Support

Tested control plane compatibility across NGINX Declarative API releases:

| Control Plane | API v5.5 | API v5.6 | API v5.7 | Notes |
| --- | --- | --- | --- | --- |
| **NGINX Instance Manager** | `2.18+` | `2.20+` | `2.22+` | Uses NMS staged configuration deployment |
| **NGINX One Console** | General availability | General availability | July 2027 | Targets NGINX One config sync groups |

---

## NGINX HTTP and Stream Servers

### Core Capabilities

| Feature | API v5.5 | API v5.6 | API v5.7 | Notes |
| --- | :---: | :---: | :---: | --- |
| **Upstreams** | ✅ | ✅ | ✅ | Custom snippets supported (inline/static or fetched from source of truth) |
| **HTTP servers** | ✅ | ✅ | ✅ | Snippets supported at `http`, `servers[]`, and `locations[]` levels |
| **TCP/UDP (`stream`) servers** | ✅ | ✅ | ✅ | Snippets supported at `streams` and `servers[]` levels |
| **TLS** | ✅ | ✅ | ✅ | Certificates and private keys can be dynamically fetched from source of truth |
| **ACME Protocol** | ✅ | ✅ | ✅ | Automated certificate issuance; see [TLS and ACME Protocol](#tls-and-acme-protocol) |
| **Client authentication** | ✅ | ✅ | ✅ | See [Client Authentication](#client-authentication) |
| **Upstream authentication** | ✅ | ✅ | ✅ | See [Upstream and Source of Truth Authentication](#upstream-and-source-of-truth-authentication) |
| **Rate limiting** | ✅ | ✅ | ✅ | Request rate enforcement for servers, locations, and API Gateway |
| **Active health checks** | ✅ | ✅ | ✅ | NGINX Plus upstream health probing |
| **Cookie-based stickiness** | ✅ | ✅ | ✅ | Session persistence for HTTP upstreams |
| **HTTP headers manipulation** | ✅ | ✅ | ✅ | **To server:** `set`, `delete` · **To client:** `add`, `delete`, `replace` |
| **Maps** | ✅ | ✅ | ✅ | Variable mapping; see [Maps](#maps) |
| **Response caching** | ✅ | ✅ | ✅ | Supported across `http`, `servers[]`, `locations[]`, and API Gateway |
| **HTTP logging** | ✅ | ✅ | ✅ | Access and error logging for `servers[]`, `locations[]`, and API Gateway |
| **HTTP access log formats** | ✅ | ✅ | ✅ | Customizable `log_format` definitions |
| **NGINX Plus REST API** | ✅ | ✅ | ✅ | Live activity monitoring and dynamic API endpoint |
| **F5 WAF for NGINX policies** | ✅ | ✅ | ✅ | Per-policy CRUD at `server`/`location` level, dataplane bundle compilation, and remote policy fetch |
| **F5 WAF for NGINX log profiles** | — | — | ✅ | Custom App Protect WAF security log profiles |

### HTTP Location Match Modifiers

Configured via `.declaration.http.servers[].locations[].urimatch` for `.declaration.http.servers[].locations[].uri`:

| Modifier | NGINX Equivalent | Behavior |
| --- | --- | --- |
| `prefix` | *(none)* | Prefix URI matching |
| `exact` | `=` | Exact URI matching |
| `regex` | `~` | Case-sensitive regular expression matching |
| `iregex` | `~*` | Case-insensitive regular expression matching |
| `best` | `^~` | Non-regex prefix match that halts regex evaluation when matched |

### HTTP Headers Manipulation

Configured under `.declaration.http.servers[].headers` and/or `.declaration.http.servers[].locations[].headers`:

| Direction | API v5.5 | API v5.6 | API v5.7 | Supported Operations |
| --- | :---: | :---: | :---: | --- |
| **Request** (client → upstream) | ✅ | ✅ | ✅ | `set` (inject/override header), `delete` (strip client header) |
| **Response** (upstream → client) | ✅ | ✅ | ✅ | `add` (append header), `delete` (strip server header), `replace` (override header) |

<details>
<summary>Configuration schema: HTTP headers object</summary>

```json
"headers": {
    "to_server": {
        "set": [
            {
                "name": "<HTTP_HEADER_NAME>",
                "value": "<VALUE_OR_NGINX_VARIABLE>"
            }
        ],
        "delete": [
            "<HTTP_HEADER_NAME>"
        ]
    },
    "to_client": {
        "add": [
            {
                "name": "<HTTP_HEADER_NAME>",
                "value": "<VALUE_OR_NGINX_VARIABLE>"
            }
        ],
        "delete": [
            "<HTTP_HEADER_NAME>"
        ],
        "replace": [
            {
                "name": "<HTTP_HEADER_NAME>",
                "value": "<VALUE_OR_NGINX_VARIABLE>"
            }
        ]
    }
}
```

</details>

### Maps

Configured via `.declaration.http.maps[].entries[].keymatch`:

| Modifier | Behavior |
| --- | --- |
| `exact` | Exact string matching |
| `regex` | Case-sensitive regular expression matching |
| `iregex` | Case-insensitive regular expression matching |

---

## NGINX API Gateway

OpenAPI and Swagger definitions can be referenced directly to provision NGINX Plus as an API Gateway with automated routing, security, and contract enforcement. Complete declaration examples are available in the [Postman collection](/contrib/postman).

### API Gateway Capabilities

| Feature | API v5.5 | API v5.6 | API v5.7 | Notes |
| --- | :---: | :---: | :---: | --- |
| **OpenAPI-driven provisioning** | ✅ | ✅ | ✅ | YAML and JSON schemas.<br>**v5.5 / v5.6:** OAS `3.0.x`<br>**v5.7:** OAS `2.0`, `3.0.x`, `3.1.x`, `3.2.x` |
| **HTTP methods enforcement** | ✅ | ✅ | ✅ | Restricts endpoints to documented HTTP methods |
| **Request body presence, `Content-Type` & schema enforcement** | — | — | ✅ | Validates presence, `Content-Type`, and OpenAPI/JSON Schema payload structure via auto-generated `njs`; see [Request Body Schema Validation](#request-body-schema-validation) |
| **Query parameter presence enforcement** | — | ✅ | ✅ | Rejects requests missing required query parameters |
| **Query parameter value enforcement** | — | ✅ | ✅ | Enforces allowed `enum` values and defaults |
| **Mandatory HTTP headers enforcement** | — | ✅ | ✅ | Rejects requests missing required request headers |
| **HTTP response codes enforcement** | — | — | ✅ | Masks undocumented upstream status codes via `proxy_intercept_errors` |
| **Per-URI rate limiting** | ✅ | ✅ | ✅ | Selective path inclusion or exclusion |
| **Per-URI client authentication** | Static JWT key, JWT JWKS URL, Bearer | Static JWT key, JWT JWKS URL, Bearer | Static JWT key, JWT JWKS URL, Bearer | Supports selective path enforcement |
| **Per-URI client authorization** | JWT claims | JWT claims | JWT claims | Regex-capable claim validation |
| **Per-URI caching** | ✅ | ✅ | ✅ | Selective path caching |
| **Developer portal** | Redocly, Backstage | Redocly, Backstage | Redocly, Backstage | Built-in portal / manifest generation |
| **API visibility** | Moesif | Moesif | Moesif | Telemetry and analytics integration |

### Request Body Schema Validation

In **API v5.7**, when `api_gateway.enforce_bodies` is enabled (`true` by default) and an operation defines a resolvable request body schema, NGINX Declarative API automatically compiles and attaches an NGINX JavaScript (`njs`) request body validator (`ngx_http_js_module` is added automatically if omitted):

- **Media types & `Content-Type` matching:**
  - Enforces required vs. optional bodies (`required: true` rejects empty bodies with HTTP `400`).
  - Matches `Content-Type` headers ignoring parameters (such as `; charset=utf-8`) and supports exact matches as well as structured suffixes and wildcards (`application/*+json`, `*+json`, `application/*`, `*/*`).
  - Structurally validates **JSON** (`application/json`, `text/json`, `*+json`), **`application/x-www-form-urlencoded`** (with schema-guided coercion for numbers, integers, booleans, and repeated array keys), and **`text/plain`**. Non-JSON/form/text payloads (e.g., XML, multipart, binary) still undergo presence and `Content-Type` validation and pass through on match.
- **JSON Schema & OpenAPI schema keywords supported:**
  - **References & structure:** Local JSON Pointer `$ref` (`#/components/schemas/...`, `#/components/requestBodies/...`, `#/definitions/...`, `#/$defs/...`), recursive/cyclic references, `$ref` sibling keywords, boolean schemas (`true`/`false`), `nullable`, `type` (single type or type array), `enum`, `const`.
  - **Objects:** `required` (automatically skipping `readOnly: true` properties in request payloads per OAS), `properties`, `patternProperties`, `additionalProperties` (`false` or schema), `minProperties` / `maxProperties`, `propertyNames`, `dependentRequired`, `dependentSchemas`, `dependencies`.
  - **Arrays:** `items`, `prefixItems` (OAS 3.1 tuples), `additionalItems`, `minItems` / `maxItems`, `uniqueItems`, `contains`, `minContains`, `maxContains`.
  - **Strings & numbers:** `minLength` / `maxLength` (Unicode code-point aware), `pattern`, `format` (`date`, `date-time`, `time`, `uuid`, `email`, `ipv4`, `ipv6`, `uri`, `hostname`, `byte`, `int32`, `int64`), `minimum` / `maximum`, boolean and numeric `exclusiveMinimum` / `exclusiveMaximum`, and decimal-safe `multipleOf`.
  - **Composition:** `allOf`, `anyOf`, `oneOf`, `not`, `if` / `then` / `else`.
- **Runtime behavior:** Invalid requests receive an HTTP `400` JSON error (`{"code": 400, "message": "..."}`); valid requests internally redirect to generated `@apigw_proxy_*` locations preserving upstream routing, `strip_uri`, authentication, headers, caching, logging, and response code enforcement.

### OpenAPI Specification Version Support

Support across OpenAPI Specification versions in **API v5.7** (YAML and JSON):

| Spec Version | Status | Supported Features | Current Limitations & Caveats |
| --- | --- | --- | --- |
| **Swagger 1.x / 1.2** | Not supported | — | Legacy `swaggerVersion` / `apis` resource-listing format is not supported |
| **OAS 2.0 (Swagger 2.0)** | Supported | • `swagger`, `info`, `paths`, response status codes<br>• Upstream URL resolution from `host`, `basePath`, and `schemes`<br>• Body presence, `Content-Type`, and schema enforcement from `in: "body"` parameters and `consumes` (operation overriding root)<br>• Local `$ref` dereferencing for body schemas (`#/definitions/...`) and parameters (`#/parameters/...`)<br>• Parameter `type` / `default` / `enum` parsing including `items` arrays | • Unresolvable local `$ref`s on request body schemas are skipped gracefully; external file/URL `$ref`s and response `$ref`s are not dereferenced<br>• When multiple `schemes` (`http`, `https`) are listed, the first `http`/`https` entry is used per host |
| **OAS 3.0.x** (`3.0.0`–`3.0.4`) | Supported | • Root, path-level, and operation-level `servers[]` with server `variables` substitution<br>• Standard HTTP methods (`GET`, `HEAD`, `POST`, `PUT`, `DELETE`, `CONNECT`, `OPTIONS`, `TRACE`, `PATCH`)<br>• Path/operation `parameters` merging (`query`/`header` enforcement and enum maps)<br>• Local `$ref` dereferencing on `requestBody`, media objects, `parameters`, and request body `schema` (`#/components/...`)<br>• Full `requestBody` schema enforcement and `responses` code enforcement | • `pathItem.$ref`, response `$ref`, and external remote `$ref`s are not dereferenced<br>• Parameter enforcement targets `required: true` `query` and `header` parameters (`cookie` and `content`-based parameters are not enforced) |
| **OAS 3.1.x** (`3.1.0`–`3.1.2`) | Supported | • All OAS `3.0.x` features in YAML and JSON<br>• Request body schemas supporting JSON Schema 2020-12 keywords (`$defs`, boolean schemas, type arrays, `const`, `prefixItems`, `dependentRequired`, `dependentSchemas`, `if`/`then`/`else`)<br>• Schemas omitting `paths` return an empty path list cleanly | • Top-level `webhooks`, `pathItem.$ref`, and response `$ref`s are not parsed<br>• Query/header parameter schemas beyond `type` / `default` / `enum` are not validated at runtime |
| **OAS 3.2.x** (`3.2.0`) | Supported | • All OAS `3.0.x` / `3.1.x` features plus optional `server.name`<br>• `additionalOperations` custom HTTP methods with path-parameter merging and sanitized NGINX variable names | • The `QUERY` HTTP method is ignored (not yet supported by NGINX)<br>• `webhooks` and `pathItem.$ref` are not parsed<br>• When `enforce_methods` generates `limit_except`, support for custom method tokens (`PURGE`, `M-SEARCH`, etc.) depends on the target NGINX binary |

> **API v5.5 & v5.6 Note:** Earlier API versions only parse top-level OAS `3.0.x` `servers[]`, standard HTTP methods, and inline `parameter.schema` definitions, and do not enforce request body schemas or response status codes.

### Configuration Reference

Declaration path: `.declaration.http.servers[].locations[].apigateway`

#### Schema, Routing, and Enforcement

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `openapi_schema` | `object` | — | Base64-encoded OpenAPI/Swagger content or remote schema URL (YAML or JSON) |
| `api_gateway.enabled` | `boolean` | `false` | Enable or disable API Gateway provisioning on this location |
| `api_gateway.strip_uri` | `boolean` | `false` | Strip the parent location `uri` prefix before forwarding requests upstream |
| `api_gateway.server_url` | `string` | `""` | Base destination URL of the upstream server (used when OpenAPI `servers` are absent or overridden) |
| `api_gateway.enforce_methods` | `boolean` | `true` | Enforce HTTP methods defined per path |
| `api_gateway.enforce_bodies` | `boolean` | `true` | Enforce mandatory request bodies, allowed `Content-Type` headers, and request body schemas |
| `api_gateway.enforce_parameters` | `boolean` | `true` | Enforce mandatory query parameters, header parameters, and enum value constraints |
| `api_gateway.enforce_response_codes` | `boolean` | `true` | Intercept and normalize undocumented upstream HTTP response status codes |

#### Path-Scoped Policies (`authentication`, `authorization`, `cache`, `rate_limit`)

| Field | Description |
| --- | --- |
| `authentication.client[]` | Client authentication profile names applied at the API Gateway level |
| `authentication.enforceOnPaths` | `true`: enforce only on `authentication.paths` · `false`: enforce on all paths except `authentication.paths` |
| `authentication.paths` | List of API endpoint paths for scoped client authentication |
| `authorization[].profile` | Authorization profile name |
| `authorization[].enforceOnPaths` | `true`: enforce only on `authorization[].paths` · `false`: enforce on all paths except `authorization[].paths` |
| `authorization[].paths` | List of API endpoint paths for scoped authorization |
| `cache[].profile` | Cache profile name |
| `cache[].enforceOnPaths` | `true`: cache only `cache[].paths` · `false`: cache all paths except `cache[].paths` |
| `cache[].paths` | List of API endpoint paths for scoped caching |
| `rate_limit.enforceOnPaths` | `true`: rate limit only `rate_limit.paths` · `false`: rate limit all paths except `rate_limit.paths` |
| `rate_limit.paths` | List of API endpoint paths for scoped rate limiting |

#### Developer Portal and Visibility Fields

| Field | Description |
| --- | --- |
| `developer_portal.enabled` | Enable or disable Developer Portal provisioning |
| `developer_portal.type` | Portal type (`redocly` or `backstage`) |
| `developer_portal.redocly.*` | Redocly configuration options — see the [Postman collection](/contrib/postman) |
| `developer_portal.backstage.*` | Backstage manifest options — see the [Postman collection](/contrib/postman) |
| `visibility[].enabled` | Enable or disable API visibility integration |
| `visibility[].type` | Integration provider (`moesif`) |
| `visibility[].moesif.*` | Moesif collector configuration — see the [Postman collection](/contrib/postman) |

### Developer Portal and API Visibility

| Integration | Category | API v5.5 | API v5.6 | API v5.7 | Notes |
| --- | --- | :---: | :---: | :---: | --- |
| **Redocly** | Developer Portal | ✅ | ✅ | ✅ | Static developer portal served directly by NGINX Plus |
| **Backstage.io** | Developer Portal | ✅ | ✅ | ✅ | Generates Backstage catalog YAML entity files |
| **Moesif** | API Visibility | ✅ | ✅ | ✅ | Telemetry integration — see [Moesif NGINX/OpenResty docs](https://www.moesif.com/docs/server-integration/nginx-openresty/) |

---

## Security and Authentication

### TLS and ACME Protocol

| Feature | API v5.5 | API v5.6 | API v5.7 | Declaration Path | NGINX Reference |
| --- | :---: | :---: | :---: | --- | --- |
| **ACME Protocol** | ✅ | ✅ | ✅ | `.declaration.http.acme_issuers[]` | [`ngx_http_acme_module`](https://nginx.org/en/docs/http/ngx_http_acme_module.html) |

<details>
<summary>Configuration schema: ACME issuer profile</summary>

```json
{
    "name": "<PROFILE_NAME>",
    "uri": "<ISSUER_URL>",
    "contact": "<CONTACT_EMAIL_ADDRESS>",
    "account_key": "<OPTIONAL_ACCOUNT_PRIVATE_KEY>",
    "ssl_trusted_certificate": "<OPTIONAL_TRUSTED_CA>",
    "ssl_verify": "<true|false>",
    "state_path": "<OPTIONAL_PATH>",
    "accept_terms_of_service": "<true|false>"
}
```

</details>

### Client Authentication

**Declaration path:**
- **API v5.5 – v5.6:** `.declaration.http.authentication.client[]`
- **API v5.7+:** `.declaration.authentication.client[]`

| Type | Description | API v5.5 | API v5.6 | API v5.7 | Scope Notes |
| --- | --- | :---: | :---: | :---: | --- |
| `jwt` | JSON Web Token (JWT) | ✅ | ✅ | ✅ | Inline JWK or remote JWKS URL |
| `mtls` | Mutual TLS | ✅ | ✅ | ✅ | Supported for HTTP servers |
| `oidc` | OpenID Connect | ✅ | ✅ | ✅ | Powered by [`ngx_http_oidc_module`](https://nginx.org/en/docs/http/ngx_http_oidc_module.html) |

<details>
<summary>Configuration schemas: JWT, mTLS, and OIDC client authentication profiles</summary>

**JWT Client Authentication Profile:**

```json
{
    "name": "<PROFILE_NAME>",
    "type": "jwt",
    "jwt": {
        "realm": "<JWT_AUTHENTICATION_REALM>",
        "key": "<JWT_KEY>|<JWT_KEY_URL>",
        "cachetime": "<OPTIONAL_JWT_KEY_CACHETIME_IN_SECONDS>",
        "token_location": "<OPTIONAL_TOKEN_LOCATION_AS_NGINX_VARIABLE>"
    }
}
```

**mTLS Client Authentication Profile:**

```json
{
    "name": "<PROFILE_NAME>",
    "type": "mtls",
    "mtls": {
        "enabled": "<on|off|optional|optional_no_ca>",
        "client_certificates": "<CLIENT_CERTIFICATES_OBJECT_NAME>",
        "trusted_ca_certificates": "<TRUSTED_CERTIFICATES_OBJECT_NAME>",
        "ocsp": {
            "enabled": "<on|off|leaf>",
            "responder": "<OCSP_RESPONDER_URL>"
        },
        "stapling": {
            "enabled": "<true|false>",
            "verify": "<true|false>",
            "responder": "<OCSP_RESPONDER_URL>"
        }
    }
}
```

**OpenID Connect (OIDC) Client Authentication Profile:**

```json
{
    "name": "<PROFILE_NAME>",
    "type": "oidc",
    "oidc": {
        "issuer": "https://<ISSUER>/realms/<REALM_NAME>",
        "client_id": "<CLIENT_ID>",
        "client_secret": "<CLIENT_SECRET>",
        "config_url": "<OPTIONAL_IDP_METADATA_URL>",
        "cookie_name": "<OPTIONAL_SESSION_COOKIE_NAME>",
        "extra_auth_args": "<OPTIONAL_EXTRA_QUERY_ARGUMENTS>",
        "redirect_uri": "<OPTIONAL_REDIRECT_URI>",
        "logout_uri": "<OPTIONAL_LOGOUT_URI>",
        "post_logout_uri": "<OPTIONAL_POST_LOGOUT_URI>",
        "logout_token_hint": "<true|false>",
        "scope": "<OPENID_SCOPE>",
        "session_store": "<OPTIONAL_SESSION_KEYVAL_STORE_NAME>",
        "session_timeout": "<OPTIONAL_OIDC_SESSION_TIMEOUT>",
        "session_sync_leeway": "<OPTIONAL_SESSION_SYNC_LEEWAY>",
        "ssl_crl": "<OPTIONAL_IDP_SSL_CRL_CERTIFICATE_PROFILE_NAME>",
        "ssl_trusted_certificate": "<OPTIONAL_IDP_SSL_TRUSTED_CA_PROFILE_NAME>",
        "userinfo": "<true|false>"
    }
}
```

</details>

### Client Authorization

**Declaration path:**
- **API v5.5 – v5.6:** `.declaration.http.authorization`
- **API v5.7+:** `.declaration.authorization`

| Type | Description | API v5.5 | API v5.6 | API v5.7 | Supported Scopes |
| --- | --- | :---: | :---: | :---: | --- |
| `jwt` | JSON Web Token (JWT) claims | ✅ | ✅ | ✅ | `.declaration.http.servers[]`, `.locations[]`, and `.apigateway` |

<details>
<summary>Configuration schema: JWT claims authorization profile</summary>

```json
{
    "name": "<PROFILE_NAME>",
    "type": "jwt",
    "jwt": {
        "claims": [
            {
                "name": "<CLAIM_NAME>",
                "value": [
                    "<AUTHORIZED_VALUE_OR_REGEXP>"
                ],
                "errorcode": "<OPTIONAL_ERROR_CODE_401_OR_403>"
            }
        ]
    }
}
```

</details>

### Upstream and Source of Truth Authentication

**Declaration path:**
- **API v5.5 – v5.6:** `.declaration.http.authentication.server[]`
- **API v5.7+:** `.declaration.authentication.server[]`

| Type | Mechanism | API v5.5 | API v5.6 | API v5.7 | Notes |
| --- | --- | :---: | :---: | :---: | --- |
| **Bearer token** | `Authorization: Bearer` header | ✅ | ✅ | ✅ | Sent to upstreams and external sources of truth |
| **Basic Auth** | `Authorization: Basic` credentials | ✅ | ✅ | ✅ | Sent to upstreams and external sources of truth |
| **HTTP header** | Custom authentication header | ✅ | ✅ | ✅ | Sent to upstreams and external sources of truth |
| **mTLS** | Client TLS certificate & key | ✅ | ✅ | ✅ | Mutual TLS to upstreams and external sources of truth |

<details>
<summary>Configuration schemas: Bearer, Basic Auth, HTTP header, and mTLS server profiles</summary>

**Bearer Token Profile:**

```json
{
    "name": "<PROFILE_NAME>",
    "type": "token",
    "token": {
        "type": "bearer",
        "token": "<AUTHENTICATION_TOKEN>"
    }
}
```

**Basic Auth Profile:**

```json
{
    "name": "<PROFILE_NAME>",
    "type": "token",
    "token": {
        "type": "basic",
        "username": "<AUTHENTICATION_USERNAME>",
        "password": "<BASE64_ENCODED_PASSWORD>"
    }
}
```

**HTTP Header Profile:**

```json
{
    "name": "<PROFILE_NAME>",
    "type": "token",
    "token": {
        "type": "header",
        "token": "<AUTHENTICATION_TOKEN>",
        "location": "<HTTP_HEADER_NAME>"
    }
}
```

**mTLS Profile:**

```json
"server": [
    {
        "name": "<PROFILE_NAME>",
        "type": "mtls",
        "mtls": {
            "certificate": "<CLIENT_CERTIFICATE>",
            "key": "<CLIENT_KEY>"
        }
    }
]
```

</details>

---

## Observability, DNS, and Scripting

### HTTP Access and Error Logging

| Feature | API v5.5 | API v5.6 | API v5.7 | Notes |
| --- | :---: | :---: | :---: | --- |
| **Access & error logging** | ✅ | ✅ | ✅ | Supported in `.declaration.http.servers[].log` and `.declaration.http.servers[].locations[].log`.<br>`condition` disables access logging when evaluating to `"0"` or `""`. |

**NGINX references:** [`access_log`](https://nginx.org/en/docs/http/ngx_http_log_module.html#access_log) · [`syslog`](https://nginx.org/en/docs/syslog.html) · [`error_log`](https://nginx.org/en/docs/ngx_core_module.html#error_log)

<details>
<summary>Configuration schema: Server / location logging object</summary>

```json
{
    "access": {
        "destination": "<LOGFILE_NAME or syslog format>",
        "format": "<OPTIONAL_ACCESS_LOG_FORMAT>",
        "condition": "<OPTIONAL_VARIABLE>"
    },
    "error": {
        "destination": "<LOGFILE_NAME or syslog format>",
        "level": "<debug|info|notice|warn|error|crit|alert|emerg>"
    }
}
```

</details>

### Access Logging Formats

| Feature | API v5.5 | API v5.6 | API v5.7 | Declaration Path | NGINX Reference |
| --- | :---: | :---: | :---: | --- | --- |
| **Custom log formats** | ✅ | ✅ | ✅ | `.declaration.http.logformats[]` | [`log_format`](https://nginx.org/en/docs/http/ngx_http_log_module.html#log_format) |

<details>
<summary>Configuration schema: HTTP access log format</summary>

```json
{
    "name": "<LOGGING_FORMAT_NAME>",
    "escape": "<DEFAULT|JSON|NONE>",
    "format": "<FORMAT STRING>"
}
```

</details>

### DNS Resolvers

| Feature | API v5.5 | API v5.6 | API v5.7 | Declaration Path | Referenceable From |
| --- | :---: | :---: | :---: | --- | --- |
| **DNS resolver profiles** | ✅ | ✅ | ✅ | `.declaration.resolvers[]` | `.declaration.http.servers[]`, `.declaration.http.upstreams[]`, `.declaration.layer4.upstreams[]` |

<details>
<summary>Configuration schema: DNS resolver profile</summary>

```json
{
    "name": "<DNS_RESOLVER_PROFILE_NAME>",
    "address": "<DNS_IP_OR_HOSTNAME>",
    "valid": "5s",
    "ipv4": true,
    "ipv6": false,
    "timeout": "30s"
}
```

</details>

### NGINX JavaScript

`njs` profiles can be supplied inline (base64-encoded under `.declaration.http.njs_profiles[]`) or fetched from a source of truth, and bound via `njs` hook arrays at `http`, `servers[]`, or `locations[]` levels. In API v5.7, API Gateway request body schema enforcement also automatically generates and wires dedicated `apigw_body_*` `njs` modules. See the [Postman collection](/contrib/postman) for full examples.

| Hook Type | API v5.5 | API v5.6 | API v5.7 | Scope Availability | NGINX Documentation |
| --- | :---: | :---: | :---: | --- | --- |
| `js_body_filter` | ✅ | ✅ | ✅ | `locations[]` | [`js_body_filter`](https://nginx.org/en/docs/http/ngx_http_js_module.html#js_body_filter) |
| `js_content` | ✅ | ✅ | ✅ | `locations[]` | [`js_content`](https://nginx.org/en/docs/http/ngx_http_js_module.html#js_content) |
| `js_header_filter` | ✅ | ✅ | ✅ | `locations[]` | [`js_header_filter`](https://nginx.org/en/docs/http/ngx_http_js_module.html#js_header_filter) |
| `js_periodic` | ✅ | ✅ | ✅ | `locations[]` | [`js_periodic`](https://nginx.org/en/docs/http/ngx_http_js_module.html#js_periodic) |
| `js_preload_object` | ✅ | ✅ | ✅ | `http`, `servers[]`, `locations[]` | [`js_preload_object`](https://nginx.org/en/docs/http/ngx_http_js_module.html#js_preload_object) |
| `js_set` | ✅ | ✅ | ✅ | `http`, `servers[]`, `locations[]` | [`js_set`](https://nginx.org/en/docs/http/ngx_http_js_module.html#js_set) |

<details>
<summary>Configuration schemas: <code>njs_profiles[]</code> definition and hook examples</summary>

**`njs` Profile:**

```json
{
    "declaration": {
        "http": {
            "njs_profiles": [
                {
                    "name": "<NJS_PROFILE_NAME>",
                    "file": {
                        "content": "<BASE64_ENCODED_JAVASCRIPT_CODE|JAVASCRIPT_FILE_URL>",
                        "authentication": [
                            {
                                "profile": "<SERVER_AUTHENTICATION_PROFILE>"
                            }
                        ]
                    }
                }
            ]
        }
    }
}
```

**`js_body_filter` Hook:**

```json
"njs": [
    {
        "hook": {
            "type": "js_body_filter",
            "js_body_filter": {
                "buffer_type": "<STRING_OR_BUFFER>"
            }
        },
        "profile": "<NJS_PROFILE_NAME>",
        "function": "<JAVASCRIPT_FUNCTION>"
    }
]
```

**`js_content`, `js_header_filter`, and `js_preload_object` Hooks:**

```json
"njs": [
    {
        "hook": {
            "type": "<js_content|js_header_filter|js_preload_object>"
        },
        "profile": "<NJS_PROFILE_NAME>",
        "function": "<JAVASCRIPT_FUNCTION>"
    }
]
```

**`js_periodic` Hook:**

```json
"njs": [
    {
        "hook": {
            "type": "js_periodic",
            "js_periodic": {
                "interval": "<INTERVAL_TIME>",
                "jitter": "<NUMBER>",
                "worker_affinity": "<MASK>"
            }
        },
        "profile": "<NJS_PROFILE_NAME>",
        "function": "<JAVASCRIPT_FUNCTION>"
    }
]
```

**`js_set` Hook:**

```json
"njs": [
    {
        "hook": {
            "type": "js_set",
            "js_set": {
                "variable": "<VARIABLE_NAME>"
            }
        },
        "profile": "<NJS_PROFILE_NAME>",
        "function": "<JAVASCRIPT_FUNCTION>"
    }
]
```

</details>
