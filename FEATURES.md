## Supported features

### NGINX `http` and `stream` servers

| Feature                    | API v4.2 | API v5.0 | API v5.1 | Notes                                                                                                                                                                                                               |
|----------------------------|----------|----------|----------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstreams                  | X        | X        | X        | <li>Snippets supported: static and from source of truth</li>                                                                                                                                                        |
| HTTP servers               | X        | X        | X        | <li>Snippets supported (`http`, `servers`, `locations`): static and from source of truth</li>                                                                                                                       |
| TCP/UDP servers            | X        | X        | X        | <li>Snippets supported (`streams`, `servers`): static and from source of truth</li>                                                                                                                                 |
| TLS                        | X        | X        | X        | <li>Certificates and keys can be dynamically fetched from source of truth (currently supported for NGINX Instance Manager)</li>                                                                                     |
| Client authentication      | X        | X        | X        | See [client authentication](#Client-authentication)                                                                                                                                                                 |
| Upstream authentication    | X        | X        | X        | See [upstream and Source of truth authentication](#Upstream-and-Source-of-truth-authentication)                                                                                                                     |
| Rate limiting              | X        | X        | X        |                                                                                                                                                                                                                     |
| Active healthchecks        | X        | X        | X        |                                                                                                                                                                                                                     |
| Cookie-based stickiness    | X        | X        | X        |                                                                                                                                                                                                                     |
| HTTP headers manipulation  | X        | X        | X        | <li>To server: set, delete</li><li>To client: add, delete, replace</li>                                                                                                                                             |
| Maps                       | X        | X        | X        |                                                                                                                                                                                                                     |
| NGINX Plus REST API access | X        | X        | X        |                                                                                                                                                                                                                     |
| NGINX App Protect WAF      | X        | X        | X        | NOTE: For NGINX Instance Manager only<li>Per-policy CRUD at `server` and `location` level</li><li>Support for dataplane-based bundle compilation</li><li>Security policies can be fetched from source of truth</li> |

### HTTP Locations

Locations `.declaration.http.servers[].locations[].uri` match modifiers in `.declaration.http.servers[].locations[].urimatch` can be:

- *prefix* - prefix URI matching
- *exact* - exact URI matching
- *regex* - case sensitive regex matching
- *iregex* - case insensitive regex matching
- *best* - case sensitive regex matching that halts any other location matching once a match is made

### NGINX API Gateway use case

| Feature                                      | API v4.2 | API v5.0 | API v5.1                                                                      | Notes                                                                         |
|----------------------------------------------|----------|----------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| Configuration generation from OpenAPI schema | X        | X        | X                                                                             |                                                                               | 
| HTTP methods enforcement                     | X        | X        | X                                                                             |                                                                               |
| per-URI rate limiting                        | X        | X        | X                                                                             |                                                                               |
| per-URI client authentication                | X        | X        | <li>Static JWT key</li><li>JWT key fetched from URL</li><li>Bearer token</li> | <li>Static JWT key</li><li>JWT key fetched from URL</li><li>Bearer token</li> |
| per-URI client authorization                 | X        | X        | <li>JWT claims</li>                                                           | <li>JWT claims</li>                                                           |

Swagger files and OpenAPI schemas can be used to automatically configure NGINX as an API Gateway

Declaration path `.declaration.http.servers[].locations[].apigateway` defines the API Gateway configuration:

- `openapi_schema` - the base64-encoded schema, or the schema URL. YAML and JSON are supported
- `api_gateway.enabled` - enable/disable API Gateway provisioning
- `api_gateway.strip_uri` - removes the `.declaration.http.servers[].locations[].uri` part of the URI before forwarding requests to the upstream
- `api_gateway.server_url` - the base URL of the upstream server
- `developer_portal.enabled` - enable/disable Developer portal provisioning
- `developer_portal.type` - developer portal type. `redocly` and `backstage` are currently supported
- `developer_portal.redocly.*` - Redocly-based developer portal parameters. See the [Postman collection](/contrib/postman)
- `developer_portal.backstage.*` - Backstage-based developer portal parameters. See the [Postman collection](/contrib/postman)
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

See the [Postman collection](/contrib/) for usage examples

### NGINX API Gateway use case - Developer Portal

| Type          | API v4.2 | API v5.0  | API v5.1 | Notes                                    |
|---------------|----------|-----------|----------|------------------------------------------|
| Redocly       | X        | X         | X        | Developer portal published by NGINX Plus |
| Backstage.io  |          | X         | X        | Backstage YAML manifest generated        |

### Client authentication

| Type | Description          | API v4.2 | API v5.0 | API v5.1                            | Notes                               |
|------|----------------------|----------|----------|-------------------------------------|-------------------------------------|
| jwt  | Java Web Token (JWT) | X        | X        | X                                   |                                     |
| mtls | Mutual TLS           | X        | X        | <li>Supported for HTTP servers</li> | <li>Supported for HTTP servers</li> |

#### Examples

Client-side authentication profiles to be defined under `.declaration.http.authentication.client[]`

- jwt client authentication profile

 ```json
{
    "name": "<PROFILE_NAME>",
    "type": "jwt",
    "jwt": {
        "realm": "<JWT_AUTHENTICATION_REALM>",
        "key": "<JWT_KEY>|<JWT_KEY_URL>",
        "cachetime": <OPTIONAL_JWT_KEY_CACHETIME_IN_SECONDS>,
        "token_location": "<OPTIONAL_TOKEN_LOCATION_AS_NGINX_VARIABLE>"
    }
}
```

- mTLS client authentication profile

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
            "enabled": <true|false>,
            "verify": <true|false>,
            "responder": "<OCSP_RESPONDER_URL>"
        }
    }
}
```

### Client authorization

| Type | Description          | API v4.2 | API v5.0 | API v5.1 | Notes                                                                                                                                                                              |
|------|----------------------|----------|----------|----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| jwt  | Java Web Token (JWT) | X        | X        | X        | Based on JWT claims. Supported under <li>.declaration.http.servers[]</li><li>.declaration.http.servers[].location[]</li><li>.declaration.http.servers[].location[].apigateway</li> |

#### Examples

Client-side authorization profiles to be defined under `.declaration.http.authorization`

- jwt client authorization profile

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
        "errorcode": <OPTIONAL_ERROR_CODE_401_OR_403>
      }
    ]
  }
}
```

### Upstream and Source of truth authentication

| Type         | Description                                  | API v4.2 | API v5.0 | API v5.1 | Notes                                                                                  |
|--------------|----------------------------------------------|----------|----------|----------|----------------------------------------------------------------------------------------|
| Bearer token | Authentication token as Authorization Bearer | X        | X        | X        | `Bearer` Authorization header is injected in requests to upstreams and source of truth |
| Basic Auth   | Authentication token as Authorization Basic  | X        | X        | X        | `Basic` Authorization header is injected in requests to upstreams and source of truth  |
| HTTP header  | Authentication token in custom HTTP header   | X        | X        | X        | HTTP header is injected in requests to upstreams and source of truth                   |
| mTLS         | Mutual TLS                                   | X        | X        | X        | Client certificate is sent to upstream / source of truth                               |

#### Examples

Server-side authentication profiles to be defined under `.declaration.http.authentication.client[]`

- Bearer token authentication profile

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

- Basic authentication profile

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

- HTTP header authentication profile

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

- mTLS authentication profile

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
```

### HTTP Headers manipulation

| Type                        | API v4.2 | API v5.0 | API v5.1 | Notes                                                                                                                        |
|-----------------------------|----------|----------|----------|------------------------------------------------------------------------------------------------------------------------------|
| Request (client to server)  | X        | X        | X        | <li>`set` - new header injection</li><li>`delete` - client header removal</li>                                               |
| Response (server to client) | X        | X        | X        | <li>`add` - new header injection</li><li>`delete` - server header removal</li><li>`replace` - server header replacement</li> |

#### Examples

To be defined under `.declaration.http.servers[].headers` and/or `.declaration.http.servers[].location[]`

```json
 "headers": {
    "to_server": {
        "set": [
            {
                "name": "<HTTP_HEADER_NAME>",
                "value": "<VALUE_OR_NGINX_VARIABLE>"
            },
            ...
        ],
        "delete": [
          "<HTTP_HEADER_NAME>",
          ...
        ]
    },
    "to_client": {
        "add": [
            {
                "name": "<HTTP_HEADER_NAME>",
                "value": "<VALUE_OR_NGINX_VARIABLE>"
            },
            ...
        ],
        "delete": [
            "<HTTP_HEADER_NAME>",
            ...
        ],
        "replace": [
            {
                "name": "<HTTP_HEADER_NAME>",
                "value": "<VALUE_OR_NGINX_VARIABLE>"
            },
            ...
        ]
    }
}
```

### NGINX Javascript

| Hook type         | API v4.2 | API v5.0 | API v5.1 | Notes                                                                                                                        |
|-------------------|----------|----------|----------|------------------------------------------------------------------------------------------------------------------------------|
| js_body_filter    | X        | X        | X        | Available in <li>`declaration.http.servers[].location[]`</li>                                                                 |
| js_content        | X        | X        | X        | Available in <li>`declaration.http.servers[].location[]`</li>                                                                 |
| js_header_filter  | X        | X        | X        | Available in <li>`declaration.http.servers[].location[]`</li>                                                                 |
| js_periodic       | X        | X        | X        | Available in <li>`declaration.http.servers[].location[]`</li>                                                                 |
| js_preload_object | X        | X        | X        | Available in <li>`.declaration.http`</li><li>`declaration.http.servers[]`</li><li>`declaration.http.servers[].location[]`</li> |
| js_set            | X        | X        | X        | Available in <li>`.declaration.http`</li><li>`declaration.http.servers[]`</li><li>`declaration.http.servers[].location[]`</li> |

Note: `njs` profiles can be included in base64-encoded format under `.declaration.http.njs[]` of fetched from an external source of truth
For detailed examples see the [Postman collection](/contrib/postman)

### Examples

`njs` profile example:

```json
{
  ...
  "declaration": {
    "http": {
      ...
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

`njs` hook examples (under `.declaration.http`, `.declaration.http.servers[]`, `.declaration.http.servers[].location[]`):

```json
"njs": [
    {
        "hook": {
            "type": "<HOOK_TYPE>"
        },
        "profile": "<NJS_PROFILE_NAME>",
        "function": "<JAVASCRIPT_FUNCTION>"
    }
]
```

Example hooks:

- `js_body_filter` - see https://nginx.org/en/docs/http/ngx_http_js_module.html#js_body_filter

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

- `js_content` - see https://nginx.org/en/docs/http/ngx_http_js_module.html#js_content

```json
"njs": [
    {
        "hook": {
            "type": "js_content"
        },
        "profile": "<NJS_PROFILE_NAME>",
        "function": "<JAVASCRIPT_FUNCTION>"
    }
]
```

- `js_header_filter` - see https://nginx.org/en/docs/http/ngx_http_js_module.html#js_header_filter

```json
"njs": [
    {
        "hook": {
            "type": "js_header_filter"
        },
        "profile": "<NJS_PROFILE_NAME>",
        "function": "<JAVASCRIPT_FUNCTION>"
    }
]
```
- `js_periodic` - see https://nginx.org/en/docs/http/ngx_http_js_module.html#js_periodic

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

- `js_preload_object` - see https://nginx.org/en/docs/http/ngx_http_js_module.html#js_preload_object

```json
"njs": [
    {
        "hook": {
            "type": "js_preload_object"
        },
        "profile": "<NJS_PROFILE_NAME>",
        "function": "<JAVASCRIPT_FUNCTION>"
    }
]
```

- `js_set` - see https://nginx.org/en/docs/http/ngx_http_js_module.html#js_set

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

### DNS resolvers

|                       | API v4.2 | API v5.0 | API v5.1 | Notes                                                                                                                              |
|-----------------------|----------|----------|----------|------------------------------------------------------------------------------------------------------------------------------------|
| DNS resolver profiles |          |          | X        | Available in <li>`declaration.http.servers[]`</li><li>`declaration.http.upstreams[]`</li><li>`declaration.layer4.upstreams[]`</li> |

#### Examples

DNS resolver profiles to be defined under `.declaration.http.resolvers[]`

- DNS resolver profile:

 ```json
{
    "name": "Google",
    "address": "8.8.8.8",
    "valid": "5s",
    "ipv4": true,
    "ipv6": false,
    "timeout": "30s"
}
```

### Maps

Map entries `.declaration.maps[].entries.keymatch` can be:

- *exact* - exact variable matching
- *regex* - case sensitive regex matching
- *iregex* - case insensitive regex matching
