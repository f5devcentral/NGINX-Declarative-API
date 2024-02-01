# Usage for API v4.2

Version 4.2 API requires:

- NGINX Instance Manager 2.14+
- NGINX Plus R30+

If NGINX App Protect declarations are used:
- NGINX App Protect Policy Compiler 4.2.0+
- NGINX Plus instances running App Protect WAF 4.2.0+ using `precompiled_publication: true` in `/etc/nginx-agent/nginx-agent.conf`

The JSON schema is self explanatory. See also the [sample Postman collection](/contrib/postman)

- `.output.type` defines how NGINX configuration will be returned:
  - *plaintext* - plaintext format
  - *json* - JSON-wrapped, base64-encoded
  - *configmap* - Kubernetes Configmap in YAML format.
    - `.output.configmap.name` must be set to the ConfigMap name
    - `.output.configmap.filename` must be set to the NGINX configuration filename
    - `.output.configmap.namespace` the optional namespace for the ConfigMap
  - *http* - NGINX configuration is POSTed to custom url
    - `.output.http.url` the URL to POST the configuration to
  - *nms* - NGINX configuration is published as a Staged Config to NGINX Instance Manager
    - `.output.nms.url` the NGINX Instance Manager URL
    - `.output.nms.username` the NGINX Instance Manager authentication username
    - `.output.nms.password` the NGINX Instance Manager authentication password
    - `.output.nms.instancegroup` the NGINX Instance Manager instance group to publish the configuration to
    - `.output.nms.synctime` **optional**, used for GitOps autosync. When specified and the declaration includes HTTP(S) references to NGINX App Protect policies, TLS certificates/keys/chains, the HTTP(S) endpoints will be checked every `synctime` seconds and if external contents have changed, the updated configuration will automatically be published to NGINX Instance Manager
    - `.output.nms.modules` an optional array of NGINX module names (ie. 'ngx_http_app_protect_module', 'ngx_http_js_module','ngx_stream_js_module')
    - `.output.nms.certificates` an optional array of TLS certificates/keys/chains to be published
      - `.output.nms.certificates[].type` the item type ('certificate', 'key', 'chain')
      - `.output.nms.certificates[].name` the certificate/key/chain name with no path/extension (ie. 'test-application')
      - `.output.nms.certificates[].contents` the content: this can be either base64-encoded or be a HTTP(S) URL that will be fetched dynamically from a source of truth
    - `.output.nms.policies[]` an optional array of NGINX App Protect security policies
      - `.output.nms.policies[].type` the policy type ('app_protect')
      - `.output.nms.policies[].name` the policy name (ie. 'prod-policy')
      - `.output.nms.policies[].active_tag` the policy tag to enable among all available versions (ie. 'v1')
      - `.output.nms.policies[].versions[]` array with all available policy versions
      - `.output.nms.policies[].versions[].tag` the policy version's tag name
      - `.output.nms.policies[].versions[].displayName` the policy version's display name
      - `.output.nms.policies[].versions[].description` the policy version's description
      - `.output.nms.policies[].versions[].contents` this can be either base64-encoded or be a HTTP(S) URL that will be fetched dynamically from a source of truth
- `.declaration` describes the NGINX configuration to be created.

### Locations ###

Locations `.declaration.http.servers[].locations[].uri` match modifiers in `.declaration.http.servers[].locations[].urimatch` can be:

- *prefix* - prefix URI matching
- *exact* - exact URI matching
- *regex* - case sensitive regex matching
- *iregex* - case insensitive regex matching
- *best* - case sensitive regex matching that halts any other location matching once a match is made

### API Gateway ###

Swagger files and OpenAPI schemas can be used to automatically configure NGINX as an API Gateway. Developer portal creation is supported through [Redocly](https://redocly.com/)

Declaration path `.declaration.http.servers[].locations[].apigateway` defines the API Gateway configuration:

- `openapi_schema` - the base64-encoded schema, or the schema URL. YAML and JSON are supported
- `api_gateway.enabled` - enable/disable API Gateway provisioning
- `api_gateway.strip_uri` - removes the `.declaration.http.servers[].locations[].uri` part of the URI before forwarding requests to the upstream
- `api_gateway.server_url` - the base URL of the upstream server
- `developer_portal.enabled` - enable/disable Developer portal provisioning
- `developer_portal.uri` - the trailing part of the Developer portal URI, this is appended to `.declaration.http.servers[].locations[].uri`. If omitted it defaults to `devportal.html`
- `authentication` - optional, used to enforce JWT authentication at the API Gateway level
- `authentication.client` - JWT authentication profile name
- `authentication.enforceOnPaths` - if set to `true` JWT authentication is enforced on all API endpoints listed under `authentication.paths`. if set to `false` JWT authentication is enforced on all API endpoints but those listed under `authentication.paths`
- `rate_limit` - optional, used to enforce rate limiting at the API Gateway level
- `rate_limit.enforceOnPaths` - if set to `true` rate limiting is enforced on all API endpoints listed under `rate_limit.paths`. if set to `false` rate limiting is enforced on all API endpoints but those listed under `rate_limit.paths`

A sample API Gateway declaration to publish the `https://petstore.swagger.io` REST API and enforce:

- REST API endpoint URIs
- HTTP Methods
- Rate limiting on `/user/login` and `/user/logout`
- JWT authentication on `/user/login` and `/usr/logout`

is:

```commandline
{
    "output": {
        "type": "nms",
        "nms": {
            "url": "{{nim_host}}",
            "username": "{{nim_username}}",
            "password": "{{nim_password}}",
            "instancegroup": "{{nim_instancegroup}}",
            "synctime": 0,
            "modules": [
                "ngx_http_js_module",
                "ngx_stream_js_module"
            ]
        }
    },
    "declaration": {
        "http": {
            "servers": [
                {
                    "name": "Petstore API",
                    "names": [
                        "apigw.nginx.lab"
                    ],
                    "resolver": "8.8.8.8",
                    "listen": {
                        "address": "80"
                    },
                    "log": {
                        "access": "/var/log/nginx/apigw.nginx.lab-access_log",
                        "error": "/var/log/nginx/apigw.nginx.lab-error_log"
                    },
                    "locations": [
                        {
                            "uri": "/petstore",
                            "urimatch": "prefix",
                            "apigateway": {
                                 "openapi_schema": {
                                    "content": "http://petstore.swagger.io/v2/swagger.json",
                                    "authentication": [
                                        {
                                            "profile": "Source of truth authentication profile using HTTP header token authentication"
                                        }
                                    ]
                                },
                                "api_gateway": {
                                    "enabled": true,
                                    "strip_uri": true,
                                    "server_url": "https://petstore.swagger.io/v2"
                                },
                                "developer_portal": {
                                    "enabled": false,
                                    "uri": "/petstore-devportal.html"
                                },
                                "authentication": {
                                    "client": [
                                        {
                                            "profile": "Petstore JWT Authentication"
                                        }
                                    ],
                                    "enforceOnPaths": true,
                                    "paths": [
                                        "/user/login",
                                        "/user/logout"
                                    ]
                                },
                                "rate_limit": [
                                    {
                                        "profile": "petstore_ratelimit",
                                        "httpcode": 429,
                                        "burst": 0,
                                        "delay": 0,
                                        "enforceOnPaths": true,
                                        "paths": [
                                            "/user/login",
                                            "/user/logout"
                                        ]
                                    }
                                ]
                            },
                            "log": {
                                "access": "/var/log/nginx/petstore-access_log",
                                "error": "/var/log/nginx/petstore-error_log"
                            }
                        }
                    ]
                }
            ],
            "rate_limit": [
                {
                    "name": "petstore_ratelimit",
                    "key": "$binary_remote_addr",
                    "size": "10m",
                    "rate": "2r/s"
                }
            ],
            "authentication": {
                "client": [
                    {
                        "name": "Petstore JWT Authentication",
                        "type": "jwt",
                        "jwt": {
                            "realm": "Petstore Authentication",
                            "key": "{\"keys\": [{\"k\":\"ZmFudGFzdGljand0\",\"kty\":\"oct\",\"kid\":\"0001\"}]}",
                            "cachetime": 5
                        }
                    }
                ],
                "server": [
                    {
                        "name": "Source of truth authentication profile using HTTP header token authentication",
                        "type": "token",
                        "token": {
                            "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImtpZCI6IjAwMDEiLCJpc3MiOiJCYXNoIEpXVCBHZW5lcmF0b3IiLCJpYXQiOjE3MDI0ODEzNjcsImV4cCI6MTcwMjQ4MTM2OH0.eyJuYW1lIjoiQm9iIERldk9wcyIsInN1YiI6IkpXVCBzdWIgY2xhaW0iLCJpc3MiOiJKV1QgaXNzIGNsYWltIiwicm9sZXMiOlsiZGV2b3BzIl19.SKA_7MszAypMEtX5NDQ0TcUbVYx_Wt0hrtmuyTmrVKU",
                            "type": "header",
                            "location": "X-AUTH-TOKEN"
                        }
                    }
                ]
            }
        }
    }
}
```

It can be tested using:

```
curl -iH "Host: apigw.nginx.lab" http://<NGINX_INSTANCE_IP_ADDRESS>/petstore/store/inventory
```

Authentication failed:

```
curl -i http://apigw.nginx.lab/petstore/user/login 
```

Authentication Succeeded:

```
curl -i http://apigw.nginx.lab/petstore/user/login -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImtpZCI6IjAwMDEiLCJpc3MiOiJCYXNoIEpXVCBHZW5lcmF0b3IiLCJpYXQiOjE3MDI0ODEzNjcsImV4cCI6MTcwMjQ4MTM2OH0.eyJuYW1lIjoiQm9iIERldk9wcyIsInN1YiI6IkpXVCBzdWIgY2xhaW0iLCJpc3MiOiJKV1QgaXNzIGNsYWltIiwicm9sZXMiOlsiZGV2b3BzIl19.SKA_7MszAypMEtX5NDQ0TcUbVYx_Wt0hrtmuyTmrVKU"
```

The API Developer portal can be accessed at:

    http://<NGINX_INSTANCE_IP_ADDRESS>/petstore/petstore-devportal.html

### Maps ###

Map entries `.declaration.maps[].entries.keymatch` can be:

- *exact* - exact variable matching
- *regex* - case sensitive regex matching
- *iregex* - case insensitive regex matching

### Snippets ###

Snippets for `http`, `upstream`, `server` and `location` can be specified as:
- base64-encoded content
- HTTP(S) URL of a source of truth to fetch snippet content from. Content on the source of truth must be plaintext
- source of truth authentication is supported through authentication profiles

### Authentication profiles ###

Client and Server authentication profiles can be defined in the declarative json at `.declaration.http.authentication`

```commandline
  "authentication": {
    "client": [
        {
            "name": "<PROFILE_NAME>",
            "type": "<PROFILE_TYPE>",
            "<PROFILE_TYPE>": {
                "<PROFILE_KEY>": "<VALUE>",
                [...]
            }
        },
        [...]
    ],
    "server": [
        {
            "name": "<PROFILE_NAME>",
            "type": "<PROFILE_TYPE>",
            "<PROFILE_TYPE>": {
                "<PROFILE_KEY>": "<VALUE>",
                [...]
            }
        },
        [...]
    ]
```

For a list of all supported authentication profile types see the [feature matrix](/FEATURES.md)

### API endpoints ###

- `POST /v4.2/config/` - Publish a new declaration
- `PATCH /v4.2/config/{config_uid}` - Update an existing declaration
  - Per-HTTP server CRUD
  - Per-HTTP upstream CRUD
  - Per-Stream server CRUD
  - Per-Stream upstream CRUD
  - Per-NGINX App Protect WAF policy CRUD
- `GET /v4.2/config/{config_uid}` - Retrieve an existing declaration
- `DELETE /v4.2/config/{config_uid}` - Delete an existing declaration

### Usage Examples ###

A sample Postman collection is available [here](/contrib/postman)