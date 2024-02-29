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
| HTTP headers manipulation  |          |          |   X      | <li>To server: set, delete</li><li>To client: add, delete, replace</li>                                                                                                        |
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

### Client authentication

| Type | Description          | API v4.0 | API v4.1 | API v4.2 | Notes                               |
|------|----------------------|----------|---------|----------|-------------------------------------|
| jwt  | Java Web Token (JWT) |          | X       | X        |                                     |
| mtls | Mutual TLS           | X        | X       | X        | <li>Supported for HTTP servers</li> |

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
        "client_certificates": "<CLIENT_CERTIFICATES_OBJECT_NAME>"
    }
}
```

### Client authorization

| Type | Description          | API v4.0 | API v4.1 | API v4.2 | Notes                                                                                                                  |
|------|----------------------|----------|----------|----------|------------------------------------------------------------------------------------------------------------------------|
| jwt  | Java Web Token (JWT) |          |          | X        | Based on JWT claims. Supported under <li>.declaration.http.server[]</li><li>.declaration.http.server[].location[]</li> |

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
          "<AUTHORIZED_VALUE>"
        ],
        "errorcode": <OPTIONAL_ERROR_CODE_401_OR_403>
      }
    ]
  }
}
```

### Upstream and Source of truth authentication

| Type         | Description                                  | API v4.0 | API v4.1 | API v4.2 | Notes                                                                                  |
|--------------|----------------------------------------------|----------|----------|----------|----------------------------------------------------------------------------------------|
| Bearer token | Authentication token as Authorization Bearer |          | X        | X        | `Bearer` Authorization header is injected in requests to upstreams and source of truth |
| Basic Auth   | Authentication token as Authorization Basic  |          |          | X        | `Basic` Authorization header is injected in requests to upstreams and source of truth  |
| HTTP header  | Authentication token in custom HTTP header   |          | X        | X        | HTTP header is injected in requests to upstreams and source of truth                   |

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

### HTTP Headers manipulation

| Type                        | API v4.0 | API v4.1 | API v4.2 | Notes                                                                                                                        |
|-----------------------------|----------|----------|----------|------------------------------------------------------------------------------------------------------------------------------|
| Request (client to server)  |          |          | X        | <li>`set` - new header injection</li><li>`delete` - client header removal</li>                                               |
| Response (server to client) |          |          | X        | <li>`add` - new header injection</li><li>`delete` - server header removal</li><li>`replace` - server header replacement</li> |

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

| Hook type         | API v4.0 | API v4.1 | API v4.2 | Notes                                                                                                                        |
|-------------------|----------|----------|----------|------------------------------------------------------------------------------------------------------------------------------|
| js_body_filter    |          |          | X        | Available in <li>`declaration.http.server[].location[]`</li>                                                                 |
| js_content        |          |          | X        | Available in <li>`declaration.http.server[].location[]`</li>                                                                 |
| js_header_filter  |          |          | X        | Available in <li>`declaration.http.server[].location[]`</li>                                                                 |
| js_periodic       |          |          | X        | Available in <li>`declaration.http.server[].location[]`</li>                                                                 |
| js_preload_object |          |          | X        | Available in <li>`.declaration.http`</li><li>`declaration.http.server[]`</li><li>`declaration.http.server[].location[]`</li> |
| js_set            |          |          | X        | Available in <li>`.declaration.http`</li><li>`declaration.http.server[]`</li><li>`declaration.http.server[].location[]`</li> |

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
            "content": "<BASE64_ENCODED_JAVASCRIPT_CODE>",
            "authentication": [
              {
                "profile": "<OPTIONAL_SERVER_AUTHENTICATION_PROFILE>"
              }
            ]
          }
        }
      ]
    }
  }
}

```

`njs` hook examples (under `.declaration.http`, `.declaration.http.server[]`, `.declaration.http.server[].location[]`):

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