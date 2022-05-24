# Usage

The JSON schema is self explainatory. See also the [sample Postman collection](/postman)

- `.output.type` defines how NGINX configuration will be returned:
  - *plaintext* - plaintext format
  - *json* - JSON-wrapped, base64-encoded
  - *configmap* - Kubernetes Configmap in YAML format.
    - `.output.configmap.name` must be set to the ConfigMap name
    - `.output.configmap.filename` must be set to the NGINX configuration filename
    - `.output.configmap.namespace` the optional namespace for the ConfigMap
  - *http* - NGINX configuration is POSTed to custom url
    - `.output.http.url` the URL to POST the configuration to
  - *nms* - NGINX configuration is published as a Staged Config to NGINX Management Suite (NMS)
    - `.output.nms.url` the NMS URL
    - `.output.nms.username` the NMS authentication username
    - `.output.nms.password` the NMS authentication password
    - `.output.nms.instancegroup` the NMS instance group to publish the configuration to
    - `.output.nms.auxfiles` an optional array of additional files to be published (ie. TLS certs, keys, ...)
      - `.output.nms.auxfiles[].name` the absolute file name, it must be under /etc/nginx
      - `.output.nms.auxfiles[].contents` the base64-encoded file contents
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
        "layer4": {
            "servers": [
                {
                    "listen": {
                        "address": "10053",
                        "protocol": "udp"
                    },
                    "upstream": "l4_upstream"
                }
            ],
            "upstreams": [
                {
                    "name": "l4_upstream",
                    "origin": [
                        {
                            "server": "10.0.0.1:53"
                        },
                        {
                            "server": "10.0.0.2:53"
                        }
                    ]
                }
            ]
        },
        "http": {
            "servers": [
                {
                    "names": [
                        "server_8080.nginx.lab",
                        "server_8081.nginx.lab"
                    ],
                    "listen": {
                        "address": "127.0.0.1:8080"
                    },
                    "log": {
                        "access": "/var/log/nginx/access_log",
                        "error": "/var/log/nginx/error_log"
                    },
                    "locations": [
                        {
                            "uri": "/test",
                            "urimatch": "exact",
                            "upstream": "http://test_upstream",
                            "health_check": {
                                "enabled": true,
                                "uri": "/healthcheck",
                                "interval": 5,
                                "fails": 3,
                                "passes": 2
                            },
                            "rate_limit": {
                                "profile": "test_ratelimit",
                                "httpcode": 429,
                                "burst": 10,
                                "delay": 3
                            },
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
                        "address": "127.0.0.1:443",
                        "http2": true,
                        "tls": {
                            "certificate": "/etc/nginx/ssl/test.crt",
                            "key": "/etc/nginx/ssl/test.key",
                            "trusted_ca": "/etc/nginx/ssl/chain.pem",
                            "ciphers": "DEFAULT",
                            "protocols": [
                                "TLSv1.2",
                                "TLSv1.3"
                            ]
                        }
                    },
                    "locations": [
                        {
                            "uri": "/",
                            "upstream": "http://test_upstream"
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
}
```
