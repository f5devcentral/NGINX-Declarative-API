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

### Javascript profiles ###

NGINX Javascript profiles are defined in `.declaration.http.njs[]`:

- `name` - the NJS profile name
- `file.content` - the base64-encoded njs source code or the `http(s)://` URL of the file
- `file.authentication.server[0].profile` - authentication profile name if `file.content` is a URL and the request must be authenticated

### Javascript hooks ###

NGINX Javascript hooks can be used in:

- `.declaration.http.njs`
  - Supported hooks:
    - `js_preload_object'
    - 'js_set`
- `.declaration.http.server[].njs`
  - Supported hooks:
    - `js_preload_object'
    - 'js_set`
- `.declaration.http.server[].location[].njs`
  - Supported hooks:
    - `js_body_filter'
    - 'js_content'
    - 'js_header_filter'
    - 'js_periodic'
    - 'js_preload_object'
    - 'js_set`

Hooks invocation is:

```
"njs": [
  {
    "hook": {
      "name": "<HOOK_NAME>",
      "parameters": [
        {
          "name": "<HOOK_PARAMETER_NAME>",
          "value": "<HOOK_PARAMETER_VALUE>"
        }
      ]
    },
    "profile": "<NGINX_JAVASCRIPT_PROFILE>",
    "function": "<JAVASCRIPT_FUNCTION_NAME>"
  }
]
```

For detailed examples see the [Postman collection](/contrib/postman)

### API Gateway ###

Swagger files and OpenAPI schemas can be used to automatically configure NGINX as an API Gateway. Developer portal creation is supported through [Redocly](https://redocly.com/)

Declaration path `.declaration.http.servers[].locations[].apigateway` defines the API Gateway configuration:

- `openapi_schema` - the base64-encoded schema, or the schema URL. YAML and JSON are supported
- `api_gateway.enabled` - enable/disable API Gateway provisioning
- `api_gateway.strip_uri` - removes the `.declaration.http.servers[].locations[].uri` part of the URI before forwarding requests to the upstream
- `api_gateway.server_url` - the base URL of the upstream server
- `developer_portal.enabled` - enable/disable Developer portal provisioning
- `developer_portal.uri` - the trailing part of the Developer portal URI, this is appended to `.declaration.http.servers[].locations[].uri`. If omitted it defaults to `devportal.html`
- `authentication` - optional, used to enforce authentication at the API Gateway level
- `authentication.client[]` - authentication profile names
- `authentication.enforceOnPaths` - if set to `true` authentication is enforced on all API endpoints listed under `authentication.paths`. if set to `false` authentication is enforced on all API endpoints but those listed under `authentication.paths`
- `authentication.paths` - paths to enforce authentication
- `authorization[]` - optional, used to enforce authorization
- `authorization[].profile` - authorization profile name
- `authorization[].enforceOnPaths` - if set to `true` authorization is enforced on all API endpoints listed under `authorization.paths`. if set to `false` authorization is enforced on all API endpoints but those listed under `authorization[].paths`
- `authorization[].paths` - paths to enforce authorization
- `rate_limit` - optional, used to enforce rate limiting at the API Gateway level
- `rate_limit.enforceOnPaths` - if set to `true` rate limiting is enforced on all API endpoints listed under `rate_limit.paths`. if set to `false` rate limiting is enforced on all API endpoints but those listed under `rate_limit.paths`

A sample API Gateway declaration to publish the `https://petstore.swagger.io` REST API and enforce:

- REST API endpoint URIs
- HTTP Methods
- Rate limiting on `/user/login`, `/usr/logout` and `/pet/{petId}/uploadImage`
- JWT authentication on `/user/login`, `/usr/logout` and `/pet/{petId}/uploadImage`
- JWT claim-based authorization on `/user/login`, `/usr/logout` and `/pet/{petId}/uploadImage`

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
                "ngx_http_app_protect_module"
            ],
            "certificates": [
                {
                    "type": "certificate",
                    "name": "test_cert",
                    "contents": {
                        "content": "{{github_gitops_root}}/v4.2/testcert.crt"
                    }
                },
                {
                    "type": "key",
                    "name": "test_key",
                    "contents": {
                        "content": "{{github_gitops_root}}/v4.2/testcert.key"
                    }
                }
            ],
            "policies": [
                {
                    "type": "app_protect",
                    "name": "production-policy",
                    "active_tag": "xss-blocked",
                    "versions": [
                        {
                            "tag": "xss-blocked",
                            "displayName": "Production Policy - XSS blocked",
                            "description": "This is a production-ready policy - XSS blocked",
                            "contents": {
                                "content": "{{github_gitops_root}}/v4.2/nap-policy-xss-blocked-bot-allowed.json"
                            }
                        },
                        {
                            "tag": "xss-allowed",
                            "displayName": "Production Policy - XSS allowed",
                            "description": "This is a production-ready policy - XSS allowed",
                            "contents": {
                                "content": "{{github_gitops_root}}/v4.2/nap-policy-xss-allowed.json"
                            }
                        }
                    ]
                }
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
                        "address": "0.0.0.0:443",
                        "http2": true,
                        "tls": {
                            "certificate": "test_cert",
                            "key": "test_key",
                            "ciphers": "DEFAULT",
                            "protocols": [
                                "TLSv1.2",
                                "TLSv1.3"
                            ]
                        }
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
                                    "content": "http://petstore.swagger.io/v2/swagger.json"
                                },
                                "api_gateway": {
                                    "enabled": true,
                                    "strip_uri": true,
                                    "server_url": "https://petstore.swagger.io/v2"
                                },
                                "developer_portal": {
                                    "enabled": true,
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
                                        "/user/logout",
                                        "/pet/{petId}/uploadImage"
                                    ]
                                },
                                "authorization": [
                                    {
                                        "profile": "JWT role based authorization",
                                        "enforceOnPaths": true,
                                        "paths": [
                                            "/user/login",
                                            "/user/logout",
                                            "/pet/{petId}/uploadImage"
                                        ]
                                    }
                                ],
                                "rate_limit": [
                                    {
                                        "profile": "petstore_ratelimit",
                                        "httpcode": 429,
                                        "burst": 0,
                                        "delay": 0,
                                        "enforceOnPaths": true,
                                        "paths": [
                                            "/user/login",
                                            "/user/logout",
                                            "/pet/{petId}/uploadImage"
                                        ]
                                    }
                                ]
                            },
                            "log": {
                                "access": "/var/log/nginx/petstore-access_log",
                                "error": "/var/log/nginx/petstore-error_log"
                            },
                            "app_protect": {
                                "enabled": true,
                                "policy": "production-policy",
                                "log": {
                                    "profile_name": "secops_dashboard",
                                    "enabled": true,
                                    "destination": "127.0.0.1:514"
                                }
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
                ]
            },
            "authorization": [
                {
                    "name": "JWT role based authorization",
                    "type": "jwt",
                    "jwt": {
                        "claims": [
                            {
                                "name": "roles",
                                "value": [
                                    "~(devops)"
                                ],
                                "errorcode": 403
                            }
                        ]
                    }
                }
            ]
        }
    }
}
```

It can be tested using:

```
curl -w '\n' -ik https://apigw.nginx.lab/petstore/store/inventory
```

Authentication failed:

```
curl -w '\n' -ik https://apigw.nginx.lab/petstore/user/login 
```

Authentication successful:

```
curl -w '\n' -ik https://apigw.nginx.lab/petstore/user/login -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImtpZCI6IjAwMDEiLCJpc3MiOiJCYXNoIEpXVCBHZW5lcmF0b3IiLCJpYXQiOjE3MDI0ODEzNjcsImV4cCI6MTcwMjQ4MTM2OH0.eyJuYW1lIjoiQm9iIERldk9wcyIsInN1YiI6IkpXVCBzdWIgY2xhaW0iLCJpc3MiOiJKV1QgaXNzIGNsYWltIiwicm9sZXMiOlsiZGV2b3BzIl19.SKA_7MszAypMEtX5NDQ0TcUbVYx_Wt0hrtmuyTmrVKU"
```

Authorization failed (based on JWT `role` claim):

```
curl -w '\n' -ki https://apigw.nginx.lab/petstore/user/login -H "Authorization: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImtpZCI6IjAwMDEiLCJpc3MiOiJCYXNoIEpXVCBHZW5lcmF0b3IiLCJpYXQiOjE3MDk3NjQ3NTMsImV4cCI6MTcwOTc2NDc1NH0.eyJuYW1lIjoiQWxpY2UgR3Vlc3QiLCJzdWIiOiJKV1Qgc3ViIGNsYWltIiwiaXNzIjoiSldUIGlzcyBjbGFpbSIsInJvbGVzIjpbImd1ZXN0Il19.jFJDq-33irz7uFxdI8c8fIb5TwTAU5BlemmIFVALUAE"
```
```
curl -w '\n' -ki https://apigw.nginx.lab/petstore/pet/1/uploadImage -X POST \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImtpZCI6IjAwMDEiLCJpc3MiOiJCYXNoIEpXVCBHZW5lcmF0b3IiLCJpYXQiOjE3MDk3NjQ3NTMsImV4cCI6MTcwOTc2NDc1NH0.eyJuYW1lIjoiQWxpY2UgR3Vlc3QiLCJzdWIiOiJKV1Qgc3ViIGNsYWltIiwiaXNzIjoiSldUIGlzcyBjbGFpbSIsInJvbGVzIjpbImd1ZXN0Il19.jFJDq-33irz7uFxdI8c8fIb5TwTAU5BlemmIFVALUAE" \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AcxV9TS0UqChYRcchQXbSLijjWKhShQqgVWnUwuX5Ck4YkxcVRcC04+LFYdXBx1tXBVRAEP0CcHZwUXaTE/yWFFjEeHPfj3b3H3TtAaFSYanbFAFWzjFQiLmayq2LwFQEI6Mc4BmVm6nOSlITn+LqHj693UZ7lfe7P0ZvLmwzwicQxphsW8QbxzKalc94nDrOSnCM+J54w6ILEj1xXXH7jXHRY4JlhI52aJw4Ti8UOVjqYlQyVeJo4klM1yhcyLuc4b3FWKzXWuid/YSivrSxzneYIEljEEiSIUFBDGRVYiNKqkWIiRftxD/+w45fIpZCrDEaOBVShQnb84H/wu1uzMDXpJoXiQODFtj9GgeAu0Kzb9vexbTdPAP8zcKW1/dUGMPtJer2tRY6Avm3g4rqtKXvA5Q4w9KTLhuxIfppCoQC8n9E3ZYGBW6Bnze2ttY/TByBNXSVvgINDYKxI2ese7+7u7O3fM63+fgB5bXKpzZcBIwAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+gFAhArKAvJglcAAAAZdEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIEdJTVBXgQ4XAAAADElEQVQI12P4//8/AAX+Av7czFnnAAAAAElFTkSuQmCC;type=image/png'
```

Authorization successful (based on JWT `role` claim):

```
curl -w '\n' -ki https://apigw.nginx.lab/petstore/user/login -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImtpZCI6IjAwMDEiLCJpc3MiOiJCYXNoIEpXVCBHZW5lcmF0b3IiLCJpYXQiOjE3MDI0ODEzNjcsImV4cCI6MTcwMjQ4MTM2OH0.eyJuYW1lIjoiQm9iIERldk9wcyIsInN1YiI6IkpXVCBzdWIgY2xhaW0iLCJpc3MiOiJKV1QgaXNzIGNsYWltIiwicm9sZXMiOlsiZGV2b3BzIl19.SKA_7MszAypMEtX5NDQ0TcUbVYx_Wt0hrtmuyTmrVKU"
```

```
curl -w '\n' -ki https://apigw.nginx.lab/petstore/pet/1/uploadImage -X POST \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImtpZCI6IjAwMDEiLCJpc3MiOiJCYXNoIEpXVCBHZW5lcmF0b3IiLCJpYXQiOjE3MDI0ODEzNjcsImV4cCI6MTcwMjQ4MTM2OH0.eyJuYW1lIjoiQm9iIERldk9wcyIsInN1YiI6IkpXVCBzdWIgY2xhaW0iLCJpc3MiOiJKV1QgaXNzIGNsYWltIiwicm9sZXMiOlsiZGV2b3BzIl19.SKA_7MszAypMEtX5NDQ0TcUbVYx_Wt0hrtmuyTmrVKU" \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AcxV9TS0UqChYRcchQXbSLijjWKhShQqgVWnUwuX5Ck4YkxcVRcC04+LFYdXBx1tXBVRAEP0CcHZwUXaTE/yWFFjEeHPfj3b3H3TtAaFSYanbFAFWzjFQiLmayq2LwFQEI6Mc4BmVm6nOSlITn+LqHj693UZ7lfe7P0ZvLmwzwicQxphsW8QbxzKalc94nDrOSnCM+J54w6ILEj1xXXH7jXHRY4JlhI52aJw4Ti8UOVjqYlQyVeJo4klM1yhcyLuc4b3FWKzXWuid/YSivrSxzneYIEljEEiSIUFBDGRVYiNKqkWIiRftxD/+w45fIpZCrDEaOBVShQnb84H/wu1uzMDXpJoXiQODFtj9GgeAu0Kzb9vexbTdPAP8zcKW1/dUGMPtJer2tRY6Avm3g4rqtKXvA5Q4w9KTLhuxIfppCoQC8n9E3ZYGBW6Bnze2ttY/TByBNXSVvgINDYKxI2ese7+7u7O3fM63+fgB5bXKpzZcBIwAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+gFAhArKAvJglcAAAAZdEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIEdJTVBXgQ4XAAAADElEQVQI12P4//8/AAX+Av7czFnnAAAAAElFTkSuQmCC;type=image/png'
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