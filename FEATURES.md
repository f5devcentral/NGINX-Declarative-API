## Supported features

### NGINX Control plane support

NGINX Declarative API has been tested with the following NGINX control plane releases:

| Control plane             | API v5.3             | API v5.4             | Notes  |
|---------------------------|----------------------|----------------------|--------|
| NGINX Instance Manager    | 2.18+                | 2.18+                |        |
| NGINX One Console         | General availability | General availability |        |


### NGINX `http` and `stream` servers

| Feature                     | API v5.3 | API v5.4 | Notes                                                                                                                                                                                                     |
|-----------------------------|----------|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstreams                   | X        | X        | <li>Snippets supported: static and from source of truth</li>                                                                                                                                              |
| HTTP servers                | X        | X        | <li>Snippets supported (`http`, `servers`, `locations`): static and from source of truth</li>                                                                                                             |
| TCP/UDP servers             | X        | X        | <li>Snippets supported (`streams`, `servers`): static and from source of truth</li>                                                                                                                       |
| TLS                         | X        | X        | <li>Certificates and keys can be dynamically fetched from source of truth</li>                                                                                                                            |
| ACME Protocol               |          | X        | See [TLS](#tls)                                                                                                                                                                                           |
| Client authentication       | X        | X        | See [client authentication](#Client-authentication)                                                                                                                                                       |
| Upstream authentication     | X        | X        | See [upstream and Source of truth authentication](#Upstream-and-Source-of-truth-authentication)                                                                                                           |
| Rate limiting               | X        | X        |                                                                                                                                                                                                           |
| Active healthchecks         | X        | X        |                                                                                                                                                                                                           |
| Cookie-based stickiness     | X        | X        |                                                                                                                                                                                                           |
| HTTP headers manipulation   | X        | X        | <li>To server: set, delete</li><li>To client: add, delete, replace</li>                                                                                                                                   |
| Maps                        | X        | X        |                                                                                                                                                                                                           |
| Cache                       | X        | X        | Supported for `http`, `servers`, `locations` and API Gateway                                                                                                                                              |
| HTTP Logging                | X        | X        | Access and error logging supported for `servers`, `locations` and API Gateway                                                                                                                             |
| HTTP access logging formats |          | X        | Customizable HTTP access logging formats                                                                                                                                                                  |
| NGINX Plus REST API access  | X        | X        |                                                                                                                                                                                                           |
| NGINX App Protect WAF       | X        | X        | NGINX Instance Manager only<li>Per-policy CRUD at `server` and `location` level</li><li>Support for dataplane-based bundle compilation</li><li>Security policies can be fetched from source of truth</li> |


### HTTP Locations

Locations `.declaration.http.servers[].locations[].uri` match modifiers in `.declaration.http.servers[].locations[].urimatch` can be:

- *prefix* - prefix URI matching
- *exact* - exact URI matching
- *regex* - case sensitive regex matching
- *iregex* - case insensitive regex matching
- *best* - case sensitive regex matching that halts any other location matching once a match is made

### NGINX API Gateway use case

| Feature                                               | API v5.3                                                                      | API v5.4                                                                      | Notes                                   |
|-------------------------------------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------|
| Configuration generation from OpenAPI schema          | X                                                                             | X                                                                             | OpenAPI 2.0, 3.0, 3.0.1                               | 
| HTTP methods enforcement                              | X                                                                             | X                                                                             |                                                       |
| per-URI rate limiting                                 | X                                                                             | X                                                                             |                                                       |
| per-URI client authentication                         | <li>Static JWT key</li><li>JWT key fetched from URL</li><li>Bearer token</li> | <li>Static JWT key</li><li>JWT key fetched from URL</li><li>Bearer token</li> |                                                       |
| per-URI client authorization                          | <li>JWT claims</li>                                                           | <li>JWT claims</li>                                                           |                                                       |
| per-URI cache                                         | X                                                                             | X                                                                             |
| Developer portal                                      | <li>Redocly</li><li>Backstage</li>                                            | <li>Redocly</li><li>Backstage</li>                                            | Supported through 3rd party integration               |
| API visibility                                        | <li>Moesif</li>                                                               | <li>Moesif</li>                                                               | Supported through 3rd party integration               |


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
- `visibility[]` - API Gateway visibility
  - `visibility[].enabled` - enable/disable API gateway visibility
  - `visibility[].type` - visibility integration type. `moesif` is currently supported
  - `visibility[].moesif.*` - Moesif visibility parameters. See the [Postman collection](/contrib/postman)
- `authentication` - optional, used to enforce authentication at the API Gateway level
- `authentication.client[]` - authentication profile names
- `authentication.enforceOnPaths` - if set to `true` authentication is enforced on all API endpoints listed under `authentication[].paths`. if set to `false` authentication is enforced on all API endpoints but those listed under `authentication.paths`
- `authentication.paths` - paths to enforce authentication on
- `authorization[]` - optional, used to enforce authorization
- `authorization[].profile` - authorization profile name
- `authorization[].enforceOnPaths` - if set to `true` authorization is enforced on all API endpoints listed under `authorization[].paths`. if set to `false` authorization is enforced on all API endpoints but those listed under `authorization[].paths`
- `authorization[].paths` - paths to enforce authorization on
- `cache[]` - optional, used to enforce authorization
- `cache[].profile` - cache profile name
- `cache[].enforceOnPaths` - if set to `true` caching is performed on all API endpoints listed under `cache[].paths`. if set to `false` caching is performed on all API endpoints but those listed under `cache[].paths`
- `cache[].paths` - paths to perform caching on
- `rate_limit` - optional, used to enforce rate limiting at the API Gateway level
- `rate_limit.enforceOnPaths` - if set to `true` rate limiting is enforced on all API endpoints listed under `rate_limit.paths`. if set to `false` rate limiting is enforced on all API endpoints but those listed under `rate_limit.paths`

See the [Postman collection](/contrib/) for usage examples

### NGINX API Gateway use case - Developer Portal

| Type            | API v5.3 | API v5.4 | Notes                                    |
|-----------------|----------|----------|------------------------------------------|
| Redocly         | X        | X        | Developer portal published by NGINX Plus |
| Backstage.io    | X        | X        | Backstage YAML manifest generated        |

### NGINX API Gateway use case - Visibility

| Type          | API v5.3 | API v5.4 | Notes                                                                                         |
|---------------|----------|----------|-----------------------------------------------------------------------------------------------|
| Moesif        | X        | X        | Integration with Moesif - see https://www.moesif.com/docs/server-integration/nginx-openresty/ |


### TLS

| Type  | Description             | API v5.3 | API v5.4 | Notes |
|-------|-------------------------|----------|----------|-------|
| ACME  | ACME Protocol support   |          | X        |       |

#### Examples

ACME issuer profiles to be defined under `.declaration.http.acme_issuers[]`
For full details for all fields see https://nginx.org/en/docs/http/ngx_http_acme_module.html 

```json
{
    "name": "<PROFILE_NAME>",
    "uri": "<ISSUER_URL>",
    "contact": "<CONTACT_EMAIL_ADDRESS>",
    "account_key": "<OPTIONAL_ACCOUNT_PRIVATE_KEY>",
    "ssl_trusted_certificate": "<OPTIONAL_TRUSTED_CA>",
    "ssl_verify": <true|false>,
    "state_path": "<OPTIONAL_PATH>",
    "accept_terms_of_service": <true|false>
}
```

### Client authentication

| Type | Description          | API v5.3 | API v5.4 | Notes                               |
|------|----------------------|----------|----------|-------------------------------------|
| jwt  | Java Web Token (JWT) | X        | X        |                                     |
| mtls | Mutual TLS           | X        | X        | <li>Supported for HTTP servers</li> |
| oidc | OpenID Connect       |          | X        | <li>Supported for HTTP servers</li> |

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

- OpenID Connect client authentication profile
For additional details see https://nginx.org/en/docs/http/ngx_http_oidc_module.html

 ```json
{
    "name": "<PROFILE_NAME>",
    "type": "oidc",
    "oidc": {
        "issuer": "https://<ISSUER>/realms/<REALM_NAME>",
        "client_id": "<CLIENT_ID>",
        "client_secret": "<CLIENT_SECRET>",
        "config_url": "<OPTIONAL_IDP_METADATA_URL>",
        "cookie_name" : "<OPTIONAL_SESSION_COOKIE_NAME>",
        "extra_auth_args": "<OPTIONAL_EXTRA_QUERY_ARGUMENTS>",
        "redirect_uri": "<OPTIONAL_REDIRECT_URI>",
        "logout_uri": "<OPTIONAL_LOGOUT_URI>",
        "post_logout_uri": "<OPTIONAL_POST_LOGOUT_URI>",
        "logout_token_hint": <true|false>,
        "scope": "<OPENID_SCOPE>",
        "session_store": "<OPTIONAL_SESSION_KEYVAL_STORE_NAME>",
        "session_timeout": "<OPTIONAL_OIDC_SESSION_TIMEOUT>",
        "ssl_crl": "<OPTIONAL_IDP_SSL_CRL_CERTIFICATE_PROFILE_NAME>",
        "ssl_trusted_certificate": "<OPTIONAL_IDP_SSL_TRUSTED_CA_PROFILE_NAME>",
        "userinfo": <true|false>
    }
}
```

### Client authorization

| Type | Description            | API v5.3 | API v5.4 | Notes                                                                                                                                                                              |
|------|------------------------|----------|----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| jwt  | Java Web Token (JWT)   | X        | X        | Based on JWT claims. Supported under <li>.declaration.http.servers[]</li><li>.declaration.http.servers[].location[]</li><li>.declaration.http.servers[].location[].apigateway</li> |

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

| Type         | Description                                    | API v5.3 | API v5.4 | Notes                                                                                  |
|--------------|------------------------------------------------|----------|----------|----------------------------------------------------------------------------------------|
| Bearer token | Authentication token as Authorization Bearer   | X        | X        | `Bearer` Authorization header is injected in requests to upstreams and source of truth |
| Basic Auth   | Authentication token as Authorization Basic    | X        | X        | `Basic` Authorization header is injected in requests to upstreams and source of truth  |
| HTTP header  | Authentication token in custom HTTP header     | X        | X        | HTTP header is injected in requests to upstreams and source of truth                   |
| mTLS         | Mutual TLS                                     | X        | X        | Client certificate is sent to upstream / source of truth                               |

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

| Type                          | API v5.3 | API v5.4 | Notes                                                                                                                        |
|-------------------------------|----------|----------|------------------------------------------------------------------------------------------------------------------------------|
| Request (client to server)    | X        | X        | <li>`set` - new header injection</li><li>`delete` - client header removal</li>                                               |
| Response (server to client)   | X        | X        | <li>`add` - new header injection</li><li>`delete` - server header removal</li><li>`replace` - server header replacement</li> |

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

| Hook type           | API v5.3 | API v5.4 | Notes                                                                                                                          |
|---------------------|----------|----------|--------------------------------------------------------------------------------------------------------------------------------|
| js_body_filter      | X        | X        | Available in <li>`declaration.http.servers[].location[]`</li>                                                                  |
| js_content          | X        | X        | Available in <li>`declaration.http.servers[].location[]`</li>                                                                  |
| js_header_filter    | X        | X        | Available in <li>`declaration.http.servers[].location[]`</li>                                                                  |
| js_periodic         | X        | X        | Available in <li>`declaration.http.servers[].location[]`</li>                                                                  |
| js_preload_object   | X        | X        | Available in <li>`.declaration.http`</li><li>`declaration.http.servers[]`</li><li>`declaration.http.servers[].location[]`</li> |
| js_set              | X        | X        | Available in <li>`.declaration.http`</li><li>`declaration.http.servers[]`</li><li>`declaration.http.servers[].location[]`</li> |

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

|                         | API v5.3 | API v5.4 | Notes                                                                                                                              |
|-------------------------|----------|----------|------------------------------------------------------------------------------------------------------------------------------------|
| DNS resolver profiles   | X        | X        | Available in <li>`declaration.http.servers[]`</li><li>`declaration.http.upstreams[]`</li><li>`declaration.layer4.upstreams[]`</li> |

#### Examples

DNS resolver profiles to be defined under `.declaration.http.resolvers[]`

- DNS resolver profile:

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

#### HTTP Access and error logging

|         | API v5.3 | API v5.4 | Notes                                                                                                                                                                                                                                 |
|---------|----------|----------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Logging | X        | X        | Available in <li>`.declaration.http.servers[].log`</li><li>`.declaration.http.servers[].locations[].log`</li><br>`condition` enables conditional logging. Logging will be disabled if `condition` evaluates to "0" or an empty string |

### Access logging formats

|                 | API v5.3 | API v5.4 | Notes |
|-----------------|----------|----------|-------|
| Logging formats |          | X        |       |


#### Examples

Access and error logging available in `.declaration.http.servers[].log` and `.declaration.http.servers[].locations[].log`
See:
* Access log: https://nginx.org/en/docs/http/ngx_http_log_module.html#access_log
* Logging to syslog: https://nginx.org/en/docs/syslog.html
* Error log: https://nginx.org/en/docs/ngx_core_module.html#error_log

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

Access logging formats to be defined in `.declaration.http.logformats[]`
See:
* Access log format: https://nginx.org/en/docs/http/ngx_http_log_module.html#log_format

```json
{
    "name": "<LOGGING_FORMAT_NAME>",
    "escape": "<DEFAULT|JSON|NONE>",
    "format": "<FORMAT STRING>"
}
```

### Maps

Map entries `.declaration.http.maps[].entries.keymatch` can be:

- *exact* - exact variable matching
- *regex* - case sensitive regex matching
- *iregex* - case insensitive regex matching