# Usage for API v1

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
  - *nms* - NGINX configuration is published as a Staged Config to NGINX Instance Manager
    - `.output.nms.url` the NMS URL
    - `.output.nms.username` the NMS authentication username
    - `.output.nms.password` the NMS authentication password
    - `.output.nms.instancegroup` the NMS instance group to publish the configuration to
    - `.output.nms.synctime` **optional**, used for GitOps autosync. When specified and the declaration includes HTTP(S) references to NGINX App Protect policies, TLS certificates/keys/chains, the HTTP(S) endpoints will be checked every `synctime` seconds and if external contents have changed, the updated configuration will automatically be published to NMS
    - `.output.nms.modules` an optional array of NGINX module names (ie. 'ngx_http_app_protect_module', 'ngx_http_js_module','ngx_stream_js_module')
    - `.output.nms.certificates` an optional array of TLS certificates/keys/chains to be published
      - `.output.nms.certificates[].type` the item type ('certificate', 'key', 'chain')
      - `.output.nms.certificates[].name` the certificate/key/chain name with no path/extension (ie. 'test-application')
      - `.output.nms.certificates[].contents` the content: this can be either base64-encoded or be a HTTP(S) URL that will be fetched dynamically
    - `.output.nms.policies` an optional array of NGINX App Protect security policies
      - `.output.nms.policies[].type` the policy type ('app_protect')
      - `.output.nms.policies[].name` the policy name (ie. 'owasp-nap-policy')
      - `.output.nms.policies.contents` the content: this can be either base64-encoded or be a HTTP(S) URL that will be fetched dynamically
    - `.output.nms.log_profiles` an optional array of NGINX App Protect log profiles policies
      - `.output.nms.log_profiles[].type` the log profile type ('app_protect')
      - `.output.nms.log_profiles[].app_protect` the NGINX App Protect log profile object
        - `.output.nms.log_profiles[].app_protect.name` the log profile name (ie. 'default_log_profile')
        - `.output.nms.log_profiles[].app_protect.format` the log profile format ('default', 'grpc', 'arcsight', 'splunk', 'user-defined')
        - `.output.nms.log_profiles[].app_protect.format_string` the log format (ie. "%date_time%|K|%ip_client%|K|%violation_rating%|K|%violations%")
        - `.output.nms.log_profiles[].app_protect.type` type of logged requests ('all', 'illegal', 'blocked')
        - `.output.nms.log_profiles[].app_protect.max_request_size` limit in bytes for the sizes of the request and request_body_base64 fields in the log. Must be smaller than max_message_size
        - `.output.nms.log_profiles[].app_protect.max_message_size` limit in KB for the total size of the message
- `.declaration` describes the NGINX configuration to be created.

### Locations ###

Locations `.declaration.http.servers[].locations[].uri` match modifiers in `.declaration.http.servers[].locations[].urimatch` can be:

- *prefix* - prefix URI matching
- *exact* - exact URI matching
- *regex* - case sensitive regex matching
- *iregex* - case insensitive regex matching
- *best* - case sensitive regex matching that halts any other location matching once a match is made

### Maps ###

Map entries `.declaration.maps[].entries.keymatch` can be:

- *exact* - exact variable matching
- *regex* - case sensitive regex matching
- *iregex* - case insensitive regex matching

A sample Postman collection can be found [here](/postman)

### Snippets ###

Snippets for http, upstream, server and location can be specified as:
- base64-encoded content
- HTTP(S) URL of a source of truth/repository to fetch snippet content from. Content must be base64-encoded

### Sample declaration ###

A sample declaration (to be POSTed to /v1/config) is:

```
{
    "output": {
        "type": "nms",
        "nms": {
            "url": "https://nim2.f5.ff.lan",
            "username": "admin",
            "password": "nimadmin",
            "instancegroup": "test-instancegroup-v2",
            "synctime": 10,
            "modules": [
                "ngx_http_app_protect_module",
                "ngx_http_js_module",
                "ngx_stream_js_module"
            ],
            "certificates": [
                {
                    "type": "certificate",
                    "name": "test_cert",
                    "contents": "http://acme.gitlab.local/test.crt"
                },
                {
                    "type": "key",
                    "name": "test_key",
                    "contents": "http://acme.gitlab.local/test.key"
                },
                {
                    "type": "chain",
                    "name": "test_chain",
                    "contents": "http://acme.gitlab.local/test.chain"
                }
            ],
            "policies": [
                {
                    "type": "app_protect",
                    "name": "test_policy",
                    "contents": "http://acme.gitlab.local/testpolicy.nap"
                }
            ],
            "log_profiles": [
                {
                    "type": "app_protect",
                    "app_protect": {
                        "name": "okta",
                        "format": "user-defined",
                        "format_string": "%date_time%|K|%ip_client%|K|%violation_rating%|K|%violations%",
                        "type": "all",
                        "max_request_size": "any",
                        "max_message_size": "5k"
                    }
                },
                {
                    "type": "app_protect",
                    "app_protect": {
                        "name": "default",
                        "format": "default",
                        "type": "all",
                        "max_request_size": "any",
                        "max_message_size": "5k"
                    }
                }
            ]
        }
    },
    "declaration": {
        "layer4": {
            "servers": [
                {
                    "listen": {
                        "address": "10053",
                        "protocol": "tcp",
                        "tls": {
                            "certificate": "test_cert",
                            "key": "test_key",
                            "chain": "test_chain",
                            "ciphers": "DEFAULT",
                            "protocols": [
                                "TLSv1.2",
                                "TLSv1.3"
                            ]
                        }
                    },
                    "upstream": "l4_upstream",
                    "snippet": "IyBUaGlzIGlzIGEgbDQgdXBzdHJlYW0gc25pcHBldCBjb21tZW50Cg=="
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
                            "app_protect": {
                                "enabled": true,
                                "policy": "test_policy",
                                "log": {
                                    "profile_name": "okta",
                                    "enabled": true,
                                    "destination": "192.168.1.5:514"
                                }
                            },
                            "snippet": "IyBUaGlzIGlzIGEgbG9jYXRpb24gc25pcHBldCBjb21tZW50Cg=="
                        }
                    ],
                    "app_protect": {
                        "enabled": true,
                        "policy": "test_policy",
                        "log": {
                            "profile_name": "default",
                            "enabled": true,
                            "destination": "192.168.1.5:514"
                        }
                    },
                    "snippet": "IyBUaGlzIGlzIGEgc2VydmVyIHNuaXBwZXQgY29tbWVudAo="
                },
                {
                    "names": [
                        "server_443"
                    ],
                    "listen": {
                        "address": "127.0.0.1:443",
                        "http2": true,
                        "tls": {
                            "certificate": "test_cert",
                            "key": "test_key",
                            "chain": "test_chain",
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
                    "snippet": "IyBUaGlzIGlzIGEgdXBzdHJlYW0gc25pcHBldCBjb21tZW50Cg=="
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
            "maps": [
                {
                    "match": "$host$request_uri",
                    "variable": "$backend",
                    "entries": [
                        {
                            "key": "www.test.lab/app1/",
                            "keymatch": "iregex",
                            "value": "upstream_1"
                        },
                        {
                            "key": "(.*).test.lab/app2/",
                            "keymatch": "regex",
                            "value": "upstream_2"
                        }
                    ]
                }
            ],
            "nginx_plus_api": {
                "write": true,
                "listen": "127.0.0.1:8080",
                "allow_acl": "0.0.0.0/0"
            },
            "snippet": "IyBUaGlzIGlzIGEgSFRUUCBzbmlwcGV0IGNvbW1lbnQK"
        }
    }
}
```
