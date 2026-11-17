# Supported Features

## Table of Contents

- [NGINX Control Plane Support](#nginx-control-plane-support)
- [NGINX `http` and `stream` Servers](#nginx-http-and-stream-servers)
  - [Core Capabilities](#core-capabilities)
  - [HTTP Locations](#http-locations)
  - [HTTP Headers Manipulation](#http-headers-manipulation)
  - [Maps](#maps)
- [NGINX API Gateway](#nginx-api-gateway)
  - [API Gateway Capabilities](#api-gateway-capabilities)
  - [OpenAPI Specification (OAS) Version Support](#openapi-specification-oas-version-support)
  - [Configuration Reference](#configuration-reference)
  - [Developer Portal Integrations](#developer-portal-integrations)
  - [API Visibility Integrations](#api-visibility-integrations)
- [Security & Authentication](#security--authentication)
  - [TLS & ACME Protocol](#tls--acme-protocol)
  - [Client Authentication](#client-authentication)
  - [Client Authorization](#client-authorization)
  - [Upstream & Source of Truth Authentication](#upstream--source-of-truth-authentication)
- [Observability, DNS & Scripting](#observability-dns--scripting)
  - [HTTP Access and Error Logging](#http-access-and-error-logging)
  - [Access Logging Formats](#access-logging-formats)
  - [DNS Resolvers](#dns-resolvers)
  - [NGINX JavaScript (`njs`)](#nginx-javascript-njs)

---

## NGINX Control Plane Support

NGINX Declarative API has been tested with the following NGINX control plane releases:

| Control Plane | API v5.5 | API v5.6 | API v5.7 | Notes |
| --- | --- | --- | --- | --- |
| NGINX Instance Manager | 2.18+ | 2.20+ | 2.22+ | |
| NGINX One Console | General availability | General availability | July 2027 | |

---

## NGINX `http` and `stream` Servers

### Core Capabilities

| Feature | API v5.5 | API v5.6 | API v5.7 | Notes |
| --- | :---: | :---: | :---: | --- |
| Upstreams | X | X | X | Snippets supported: static and from source of truth |
| HTTP servers | X | X | X | Snippets supported (`http`, `servers`, `locations`): static and from source of truth |
| TCP/UDP servers | X | X | X | Snippets supported (`streams`, `servers`): static and from source of truth |
| TLS | X | X | X | Certificates and keys can be dynamically fetched from source of truth |
| ACME Protocol | X | X | X | See [TLS & ACME Protocol](#tls--acme-protocol) |
| Client authentication | X | X | X | See [Client Authentication](#client-authentication) |
| Upstream authentication | X | X | X | See [Upstream & Source of Truth Authentication](#upstream--source-of-truth-authentication) |
| Rate limiting | X | X | X | |
| Active healthchecks | X | X | X | |
| Cookie-based stickiness | X | X | X | |
| HTTP headers manipulation | X | X | X | **To server:** `set`, `delete`<br>**To client:** `add`, `delete`, `replace` |
| Maps | X | X | X | See [Maps](#maps) |
| Cache | X | X | X | Supported for `http`, `servers`, `locations`, and API Gateway |
| HTTP Logging | X | X | X | Access and error logging supported for `servers`, `locations`, and API Gateway |
| HTTP access logging formats | X | X | X | Customizable HTTP access logging formats |
| NGINX Plus REST API access | X | X | X | |
| F5 WAF for NGINX policies | X | X | X | • Per-policy CRUD at `server` and `location` level<br>• Support for dataplane-based bundle compilation<br>• Security policies can be fetched from source of truth |
| F5 WAF for NGINX log profiles | | | X | |

### HTTP Locations

Location match modifiers in `.declaration.http.servers[].locations[].urimatch` for `.declaration.http.servers[].locations[].uri`:

| Modifier | Description |
| --- | --- |
| `prefix` | Prefix URI matching |
| `exact` | Exact URI matching |
| `regex` | Case-sensitive regex matching |
| `iregex` | Case-insensitive regex matching |
| `best` | Case-sensitive regex matching that halts further location matching once matched |

### HTTP Headers Manipulation

| Direction | API v5.5 | API v5.6 | API v5.7 | Supported Operations |
| --- | :---: | :---: | :---: | --- |
| Request (client to server) | X | X | X | • `set` — new header injection<br>• `delete` — client header removal |
| Response (server to client) | X | X | X | • `add` — new header injection<br>• `delete` — server header removal<br>• `replace` — server header replacement |

**Configuration paths:** `.declaration.http.servers[].headers` and/or `.declaration.http.servers[].locations[]`

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

### Maps

Map entry match modifiers in `.declaration.http.maps[].entries.keymatch`:

| Modifier | Description |
| --- | --- |
| `exact` | Exact variable matching |
| `regex` | Case-sensitive regex matching |
| `iregex` | Case-insensitive regex matching |

---

## NGINX API Gateway

Swagger files and OpenAPI schemas can be used to automatically provision NGINX as an API Gateway. See the [Postman collection](/contrib/postman) for complete usage examples.

### API Gateway Capabilities

| Feature | API v5.5 | API v5.6 | API v5.7 | Notes |
| --- | :---: | :---: | :---: | --- |
| Configuration generation from OpenAPI schema | X | X | X | YAML and JSON format.<br>**v5.5 / v5.6:** OAS `3.0.x`<br>**v5.7:** OAS `2.0`, `3.0.x`, `3.1.x`, `3.2.x` |
| HTTP methods enforcement | X | X | X | |
| Request payload enforcement | | | X | |
| Query string parameters enforcement | | X | X | |
| Query string parameter values enforcement | | X | X | |
| Mandatory HTTP headers enforcement | | X | X | |
| HTTP response codes enforcement | | | X | |
| Per-URI rate limiting | X | X | X | |
| Per-URI client authentication | Static JWT key, JWT key from URL, Bearer token | Static JWT key, JWT key from URL, Bearer token | Static JWT key, JWT key from URL, Bearer token | |
| Per-URI client authorization | JWT claims | JWT claims | JWT claims | |
| Per-URI cache | X | X | X | |
| Developer portal | Redocly, Backstage | Redocly, Backstage | Redocly, Backstage | 3rd-party integration |
| API visibility | Moesif | Moesif | Moesif | 3rd-party integration |

### OpenAPI Specification (OAS) Version Support

Support across OpenAPI Specification versions in **API v5.7** (YAML and JSON):

| Spec Version | Status | Supported Features | Known Gaps / Caveats |
| --- | --- | --- | --- |
| **Swagger 1.x / 1.2** | Not supported | — | `swaggerVersion` / `apis` format is not supported |
| **OAS 2.0 (Swagger 2.0)** | Supported | • `swagger`, `info`, `paths`, response status codes<br>• Upstream URL resolution from `host`, `basePath`, and `schemes`<br>• Body enforcement from `in: "body"` parameters and `consumes` (operation overriding root)<br>• Direct and `items` array `type` / `default` / `enum` parsing on parameters | • `$ref` objects (e.g., `#/parameters/...`, `#/responses/...`) are not dereferenced<br>• When multiple `schemes` (`http`, `https`) are listed, the first `http`/`https` scheme is used per host |
| **OAS 3.0.x** (`3.0.0`–`3.0.4`) | Supported | • Root `servers[]`, per-path `servers[]`, and per-operation `servers[]` with server `variables` substitution<br>• Standard HTTP methods (`GET`, `HEAD`, `POST`, `PUT`, `DELETE`, `CONNECT`, `OPTIONS`, `TRACE`, `PATCH`)<br>• Path/operation `parameters` merging (`query`/`header` enforcement and enum maps)<br>• `requestBody` enforcement and `responses` code enforcement | • `$ref` objects on path items, parameters, request bodies, or responses are not dereferenced<br>• Parameter enforcement targets `required: true` `query` and `header` parameters (`cookie` and `content`-based parameters are not enforced) |
| **OAS 3.1.x** (`3.1.0`–`3.1.2`) | Supported | • All OAS `3.0.x` features in YAML and JSON<br>• Schemas omitting `paths` return an empty path list | • Top-level `webhooks` and `pathItem.$ref` / parameter `$ref` are not parsed or dereferenced<br>• JSON Schema 2020-12 keywords beyond `type` / `default` / `enum` are not enforced |
| **OAS 3.2.x** (`3.2.0`) | Supported | • All OAS `3.0.x` / `3.1.x` features plus optional `server.name`<br>• `additionalOperations` custom HTTP methods with path-parameter merging and NGINX variable name sanitization | • The `QUERY` HTTP method is ignored (not yet supported by NGINX)<br>• `webhooks` and `$ref` are not parsed or dereferenced<br>• When `enforce_methods` generates `limit_except`, runtime NGINX support for custom method keywords (`PURGE`, `M-SEARCH`, etc.) depends on the target NGINX build |

> **API v5.5 & v5.6 Note:** Versions prior to `v5.7` only parse top-level OAS `3.0.x` `servers[]`, standard HTTP methods, and inline `parameter.schema` definitions.

### Configuration Reference

Declaration path: `.declaration.http.servers[].locations[].apigateway`

#### Schema, Routing & Enforcement

| Field | Description |
| --- | --- |
| `openapi_schema` | Base64-encoded schema or schema URL (YAML and JSON supported) |
| `api_gateway.enabled` | Enable/disable API Gateway provisioning |
| `api_gateway.strip_uri` | Strip the location `uri` prefix before forwarding requests upstream |
| `api_gateway.server_url` | Base destination URL of the upstream server (fallback/override) |
| `api_gateway.enforce_methods` | Enable/disable HTTP methods enforcement (`true` by default) |
| `api_gateway.enforce_bodies` | Enable/disable request bodies and `Content-Type` enforcement (`true` by default) |
| `api_gateway.enforce_parameters` | Enable/disable mandatory query string parameters and HTTP headers enforcement (`true` by default) |
| `api_gateway.enforce_response_codes` | Enable/disable HTTP response codes enforcement (`true` by default) |

#### Developer Portal & Visibility

| Field | Description |
| --- | --- |
| `developer_portal.enabled` | Enable/disable Developer Portal provisioning |
| `developer_portal.type` | Developer Portal type (`redocly` or `backstage`) |
| `developer_portal.redocly.*` | Redocly configuration parameters — see the [Postman collection](/contrib/postman) |
| `developer_portal.backstage.*` | Backstage configuration parameters — see the [Postman collection](/contrib/postman) |
| `visibility[].enabled` | Enable/disable API Gateway visibility |
| `visibility[].type` | Visibility integration type (`moesif`) |
| `visibility[].moesif.*` | Moesif visibility parameters — see the [Postman collection](/contrib/postman) |

#### Path-Scoped Policies (`authentication`, `authorization`, `cache`, `rate_limit`)

| Field | Description |
| --- | --- |
| `authentication.client[]` | Optional client authentication profile names at the API Gateway level |
| `authentication.enforceOnPaths` | `true`: enforce only on `authentication.paths`; `false`: enforce on all endpoints except `authentication.paths` |
| `authentication.paths` | API endpoint paths for authentication enforcement |
| `authorization[].profile` | Authorization profile name |
| `authorization[].enforceOnPaths` | `true`: enforce only on `authorization[].paths`; `false`: enforce on all endpoints except `authorization[].paths` |
| `authorization[].paths` | API endpoint paths for authorization enforcement |
| `cache[].profile` | Cache profile name |
| `cache[].enforceOnPaths` | `true`: cache only `cache[].paths`; `false`: cache all endpoints except `cache[].paths` |
| `cache[].paths` | API endpoint paths for caching |
| `rate_limit.enforceOnPaths` | `true`: rate limit only `rate_limit.paths`; `false`: rate limit all endpoints except `rate_limit.paths` |
| `rate_limit.paths` | API endpoint paths for rate limiting |

### Developer Portal Integrations

| Type | API v5.5 | API v5.6 | API v5.7 | Notes |
| --- | :---: | :---: | :---: | --- |
| Redocly | X | X | X | Developer portal published by NGINX Plus |
| Backstage.io | X | X | X | Backstage YAML manifest generated |

### API Visibility Integrations

| Type | API v5.5 | API v5.6 | API v5.7 | Notes |
| --- | :---: | :---: | :---: | --- |
| Moesif | X | X | X | Integration with Moesif — see [Moesif NGINX/OpenResty docs](https://www.moesif.com/docs/server-integration/nginx-openresty/) |

---

## Security & Authentication

### TLS & ACME Protocol

| Type | Description | API v5.5 | API v5.6 | API v5.7 |
| --- | --- | :---: | :---: | :---: |
| ACME | ACME Protocol support | X | X | X |

**Declaration path:** `.declaration.http.acme_issuers[]`
**NGINX reference:** [ngx_http_acme_module](https://nginx.org/en/docs/http/ngx_http_acme_module.html)

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

### Client Authentication

| Type | Description | API v5.5 | API v5.6 | API v5.7 | Notes |
| --- | --- | :---: | :---: | :---: | --- |
| `jwt` | JSON Web Token (JWT) | X | X | X | |
| `mtls` | Mutual TLS | X | X | X | Supported for HTTP servers |
| `oidc` | OpenID Connect | X | X | X | Supported for HTTP servers |

**Declaration path:**
- API v5.5 – v5.6: `.declaration.http.authentication.client[]`
- API v5.7+: `.declaration.authentication.client[]`

#### JWT Client Authentication Profile

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

#### mTLS Client Authentication Profile

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

#### OpenID Connect (OIDC) Client Authentication Profile

NGINX reference: [ngx_http_oidc_module](https://nginx.org/en/docs/http/ngx_http_oidc_module.html)

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

### Client Authorization

| Type | Description | API v5.5 | API v5.6 | API v5.7 | Notes |
| --- | --- | :---: | :---: | :---: | --- |
| `jwt` | JSON Web Token (JWT) claims | X | X | X | Supported under `.declaration.http.servers[]`, `.declaration.http.servers[].locations[]`, and `.declaration.http.servers[].locations[].apigateway` |

**Declaration path:**
- API v5.5 – v5.6: `.declaration.http.authorization`
- API v5.7+: `.declaration.authorization`

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

### Upstream & Source of Truth Authentication

| Type | Description | API v5.5 | API v5.6 | API v5.7 | Notes |
| --- | --- | :---: | :---: | :---: | --- |
| Bearer token | `Authorization: Bearer` token | X | X | X | Injected in requests to upstreams and source of truth |
| Basic Auth | `Authorization: Basic` credentials | X | X | X | Injected in requests to upstreams and source of truth |
| HTTP header | Custom HTTP authentication header | X | X | X | Injected in requests to upstreams and source of truth |
| mTLS | Mutual TLS | X | X | X | Client certificate sent to upstream / source of truth |

**Declaration path:**
- API v5.5 – v5.6: `.declaration.http.authentication.server[]`
- API v5.7+: `.declaration.authentication.server[]`

#### Bearer Token Profile

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

#### Basic Auth Profile

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

#### HTTP Header Profile

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

#### mTLS Profile

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

---

## Observability, DNS & Scripting

### HTTP Access and Error Logging

| Feature | API v5.5 | API v5.6 | API v5.7 | Notes |
| --- | :---: | :---: | :---: | --- |
| Logging | X | X | X | Available in `.declaration.http.servers[].log` and `.declaration.http.servers[].locations[].log`.<br>`condition` enables conditional logging (disabled when evaluating to `"0"` or `""`). |

NGINX references:
- Access log: [ngx_http_log_module#access_log](https://nginx.org/en/docs/http/ngx_http_log_module.html#access_log)
- Syslog logging: [syslog](https://nginx.org/en/docs/syslog.html)
- Error log: [ngx_core_module#error_log](https://nginx.org/en/docs/ngx_core_module.html#error_log)

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

### Access Logging Formats

| Feature | API v5.5 | API v5.6 | API v5.7 |
| --- | :---: | :---: | :---: |
| Logging formats | X | X | X |

**Declaration path:** `.declaration.http.logformats[]`
**NGINX reference:** [ngx_http_log_module#log_format](https://nginx.org/en/docs/http/ngx_http_log_module.html#log_format)

```json
{
    "name": "<LOGGING_FORMAT_NAME>",
    "escape": "<DEFAULT|JSON|NONE>",
    "format": "<FORMAT STRING>"
}
```

### DNS Resolvers

| Feature | API v5.5 | API v5.6 | API v5.7 | Supported In |
| --- | :---: | :---: | :---: | --- |
| DNS resolver profiles | X | X | X | `.declaration.http.servers[]`, `.declaration.http.upstreams[]`, `.declaration.layer4.upstreams[]` |

**Declaration path:** `.declaration.http.resolvers[]`

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

### NGINX JavaScript (`njs`)

| Hook Type | API v5.5 | API v5.6 | API v5.7 | Scope Availability | NGINX Documentation |
| --- | :---: | :---: | :---: | --- | --- |
| `js_body_filter` | X | X | X | `locations[]` | [js_body_filter](https://nginx.org/en/docs/http/ngx_http_js_module.html#js_body_filter) |
| `js_content` | X | X | X | `locations[]` | [js_content](https://nginx.org/en/docs/http/ngx_http_js_module.html#js_content) |
| `js_header_filter` | X | X | X | `locations[]` | [js_header_filter](https://nginx.org/en/docs/http/ngx_http_js_module.html#js_header_filter) |
| `js_periodic` | X | X | X | `locations[]` | [js_periodic](https://nginx.org/en/docs/http/ngx_http_js_module.html#js_periodic) |
| `js_preload_object` | X | X | X | `http`, `servers[]`, `locations[]` | [js_preload_object](https://nginx.org/en/docs/http/ngx_http_js_module.html#js_preload_object) |
| `js_set` | X | X | X | `http`, `servers[]`, `locations[]` | [js_set](https://nginx.org/en/docs/http/ngx_http_js_module.html#js_set) |

> **Note:** `njs` profiles can be supplied base64-encoded under `.declaration.http.njs_profiles[]` or fetched from an external source of truth. See the [Postman collection](/contrib/postman) for full examples.

#### `njs` Profile Example

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

#### `njs` Hook Configuration Examples

Hooks are configured under `.declaration.http`, `.declaration.http.servers[]`, or `.declaration.http.servers[].locations[]`:

**`js_body_filter`:**

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

**`js_content`, `js_header_filter`, and `js_preload_object`:**

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

**`js_periodic`:**

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

**`js_set`:**

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
