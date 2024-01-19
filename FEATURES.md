## Supported features

### NGINX `http` and `stream` servers

Currently supported features:

| Feature                    | API v3.1                                                                                | Notes                                                                      |
|----------------------------|-----------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| Upstreams                  | CRUD                                                                                    | Snippets supported: static and from source of truth                        |
| HTTP servers               | CRUD                                                                                    | Snippets supported (`http`, `servers`, `locations`): static and from source of truth |
| TCP/UDP servers            | CRUD                                                                                    | Snippets supported (`streams`, `servers`): static and from source of truth |
| TLS                        | CRUD                                                                                    | Certificates and keys can be dynamically fetched from source of truth      |
| mTLS                       | CRUD                                                                                    | Certificates and keys can be dynamically fetched from source of truth      |
| Rate limiting              | X                                                                                       |                                                                            |
| Active healthchecks        | X                                                                                       |                                                                            |
| Cookie-based stickiness    | X                                                                                       |                                                                            |
| Maps                       | X                                                                                       |                                                                            |
| NGINX Plus REST API access | X                                                                                       |                                                                            |
| NGINX App Protect WAF      | Per-policy CRUD at `server` and `location` level with dataplane-based bundle compilation | Security policies can be dynamically fetched from source of truth          |

### API Gateway use case

Currently supported features:

| Feature                    | API v3.1                                                                                | Notes                                                                                                                                                                              |
|----------------------------|-----------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| API Gateway                | Swagger and OpenAPI YAML and JSON schema support                                        | <li>Automated configuration</li><li>HTTP methods enforcement</li><li>per-URI rate limiting</li><li>per-URI JWT authentication: JWT key hardwired or referenced as HTTP(S) URL</li> |
| API Developer Portal       | Swagger and OpenAPI YAML and JSON schema support                                        | Based on Redocly                                                                                                                                                                   |
