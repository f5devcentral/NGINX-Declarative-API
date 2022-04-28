# Usage

The JSON schema is self explainatory.

- `.output.type` defines how NGINX configuration will be returned:
  - *plaintext* - plaintext format
  - *json* - JSON-wrapped, base64-encoded
  - *configmap* - Kubernetes Configmap in YAML format.
    - `.output.configmap.name` must be set to the ConfigMap name
    - `.output.configmap.filename` must be set to the NGINX configuration filename
- `.declaration` describes the NGINX configuration to be created.

Locations `.declaration.servers[].locations[].uri` match modifiers in `.declaration.servers[].locations[].urimatch` can be:

- *prefix* - prefix URI matching
- *exact* - exact URI matching
- *regex* - case sensitive regex matching
- *iregex* - case insensitive regex matching
- *best* - case sensitive regex matching that halts any other location matching once a match is made

A sample Postman collection can be found [here](/postman)

A sample declaration (to be POSTed to /v0/config) is:

```
{
    "output": {
        "type": "plaintext"
    },
    "declaration": {
        "servers": [
            {
                "names": [
                    "server_8080.nginx.lab",
                    "server_8081.nginx.lab"
                ],
                "listen": {
                    "address": "192.168.123.1:8080"
                },
                "log": {
                    "access": "/var/log/nginx/access_log",
                    "error": "/var/log/nginx/error_log"
                },
                "locations": [
                    {
                        "uri": "/admin/(.*)$",
                        "urimatch": "casesens_regex",
                        "upstream": "test_upstream",
                        "caching": "test_caching",
                        "rate_limit": {
                            "profile": "test_ratelimit",
                            "httpcode": 429,
                            "burst": 10,
                            "delay": 3
                        },
                        "health_check": true
                    },
                    {
                        "uri": "/test",
                        "urimatch": "exact",
                        "upstream": "test_upstream2",
                        "caching": "test_caching",
                        "health_check": true,
                        "snippet": "# This is a location snippet comment"
                    }
                ],
                "snippet": "# This is a server snippet comment"
            },
            {
                "names": [
                    "server_443"
                ],
                "listen": {
                    "address": "192.168.123.2:443",
                    "http2": true,
                    "tls": {
                        "certificate": "/etc/nginx/ssl/test.crt",
                        "key": "/etc/nginx/ssl/test.key",
                        "trusted_ca": "/etc/nginx/ssl/chain.pem",
                        "ciphers": "TLS_AES_256_GCM_SHA384:!ECDHE-RSA-AES256-SHA384:!aNULL:!eNULL:!LOW:!RC4:!3DES:!MD5:!EXP:!PSK:!SRP:!DSS",
                        "protocols": [
                            "TLSv1.2",
                            "TLSv1.3"
                        ]
                    }
                },
                "locations": [
                    {
                        "uri": "/",
                        "upstream": "test_upstream"
                    }
                ]
            }
        ],
        "upstreams": [
            {
                "name": "test_upstream",
                "origin": [
                    {
                        "server": "10.0.0.1:80",
                        "weight": 5,
                        "max_fails": 2,
                        "fail_timeout": "30s",
                        "max_conns": 3,
                        "slow_start": "30s"
                    },
                    {
                        "server": "10.0.0.2:80",
                        "backup": true
                    }
                ],
                "sticky": {
                    "cookie": "cookie_name",
                    "expires": "1h",
                    "domain": ".testserver",
                    "path": "/"
                },
                "snippet": "# This is a upstream snippet comment"
            }
        ],
        "rate_limit": [
            {
                "name": "test_ratelimit",
                "key": "$binary_remote_addr",
                "size": "10m",
                "rate": "1r/s"
            }
        ],
        "nginx_plus_api": {
            "write": true,
            "listen": "127.0.0.1:8080",
            "allow_acl": "192.168.1.0/24"
        }
    }
}
```
