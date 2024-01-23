## Supported features

### NGINX `http` and `stream` servers

| Feature                    | API v3.1 | API v4.0 | Notes                                                                                                                                                                              |
|----------------------------|----------|---------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstreams                  | CRUD     | CRUD    | <li>Snippets supported: static and from source of truth</li>                                                                                                                       |
| HTTP servers               | CRUD     | CRUD    | <li>Snippets supported (`http`, `servers`, `locations`): static and from source of truth</li>                                                                                      |
| TCP/UDP servers            | CRUD     | CRUD    | <li>Snippets supported (`streams`, `servers`): static and from source of truth</li>                                                                                                |
| TLS                        | CRUD     | CRUD    | <li>Certificates and keys can be dynamically fetched from source of truth</li>                                                                                                     |
| mTLS                       | CRUD     | CRUD    | <li>Certificates and keys can be dynamically fetched from source of truth</li>                                                                                                     |
| JWT client authentication  |          | X       | <li>JWT key can be hardwired or fetched from source of truth</li>                                                                                                                  |
| Rate limiting              | X        | X       |                                                                                                                                                                                    |
| Active healthchecks        | X        | X       |                                                                                                                                                                                    |
| Cookie-based stickiness    | X        | X       |                                                                                                                                                                                    |
| Maps                       | X        | X       |                                                                                                                                                                                    |
| NGINX Plus REST API access | X        | X       |                                                                                                                                                                                    |
| NGINX App Protect WAF      | X        | X       | <li>Per-policy CRUD at `server` and `location` level</li><li>Support for dataplane-based bundle compilation</li><li>Security policies can be fetched from source of truth</li>     |


### API Gateway

| Feature                                      | API v3.1 | API v4.0 | Notes                                                    |
|----------------------------------------------|----------|----------|----------------------------------------------------------|
| Configuration generation from OpenAPI schema | X        | X        |                                                          | 
| HTTP methods enforcement                     | X        | X        |                                                          |
| per-URI rate limiting                        | X        | X        |                                                          |
| per-URI JWT authentication                   | X        | X        | JWT key can be hardwired or fetched from source of truth |


### API Gateway - Developer Portal

| Feature                                         | API v3.1 | API v4.0 | Notes                                                                                                                                                                              |
|-------------------------------------------------|----------|----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Developer Portal generation from OpenAPI schema | X        | X        | <li>Based on Redocly</li>                                 |
