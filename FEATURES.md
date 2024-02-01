## Supported features

### NGINX `http` and `stream` servers

| Feature                    | API v4.0 | API v4.1 | API v4.2 | Notes                                                                                                                                                                          |
|----------------------------|----------|----------|----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstreams                  | CRUD     | CRUD     | CRUD     | <li>Snippets supported: static and from source of truth</li>                                                                                                                   |
| HTTP servers               | CRUD     | CRUD     | CRUD     | <li>Snippets supported (`http`, `servers`, `locations`): static and from source of truth</li>                                                                                  |
| TCP/UDP servers            | CRUD     | CRUD     | CRUD     | <li>Snippets supported (`streams`, `servers`): static and from source of truth</li>                                                                                            |
| TLS                        | CRUD     | CRUD     | CRUD     | <li>Certificates and keys can be dynamically fetched from source of truth</li>                                                                                                 |
| Client authentication      | X        | X        | X        | See [client authentication profiles](#Client-authentication-profiles)                                                                                                          |
| Server authentication      | X        | X        | X        | See [server authentication profiles](#Upstream-and-Source-of-truth-authentication-profiles)                                                                                    |
| Rate limiting              | X        | X        | X        |                                                                                                                                                                                |
| Active healthchecks        | X        | X        | X        |                                                                                                                                                                                |
| Cookie-based stickiness    | X        | X        | X        |                                                                                                                                                                                |
| Maps                       | X        | X        | X        |                                                                                                                                                                                |
| NGINX Plus REST API access | X        | X        | X        |                                                                                                                                                                                |
| NGINX App Protect WAF      | X        | X        | X        | <li>Per-policy CRUD at `server` and `location` level</li><li>Support for dataplane-based bundle compilation</li><li>Security policies can be fetched from source of truth</li> |

### API Gateway

| Feature                                      | API v4.0 | API v4.1 | API v4.2 | Notes                                                                                     |
|----------------------------------------------|----------|----------|----------|-------------------------------------------------------------------------------------------|
| Configuration generation from OpenAPI schema | X        | X        | X        |                                                                                           | 
| HTTP methods enforcement                     | X        | X        | X        |                                                                                           |
| per-URI rate limiting                        | X        | X        | X        |                                                                                           |
| per-URI client authentication                | X        | X        | X        | <li>Static JWT key</li><li>JWT key fetched from URL</li><li>Bearer token</li> |

### API Gateway - Developer Portal

| Feature                                         | API v4.0 | API v4.1 | API v4.2 | Notes                     |
|-------------------------------------------------|----------|----------|----------|---------------------------|
| Developer Portal generation from OpenAPI schema | X        | X        | X        | <li>Based on Redocly</li> |

### Client authentication profiles

| Type | Description          | API v4.0 | API v4.1 | API v4.2 | Notes                               |
|------|----------------------|----------|----------|----------|-------------------------------------|
| jwt  | Java Web Token (JWT) |          | X        | X        |                                     |
| mtls | Mutual TLS           | X        |  X       |  X       | <li>Supported for HTTP servers</li> |

### Upstream and Source of truth authentication profiles

| Type  | Description                                      | API v4.0 | API v4.1 | API v4.2 | Notes |
|-------|--------------------------------------------------|----------|----------|----------|-------|
| token | <li>Bearer token</li><li>Custom HTTP header</li> |          | X        | X        |       |
