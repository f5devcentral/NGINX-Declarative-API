# Usage for NGINX Declarative API v5.3

Version 5.3 supports:

- [NGINX Instance Manager](https://docs.nginx.com/nginx-management-suite/nim/) 2.14+. Version 2.18+ is required for NGINX R33 and above
- [NGINX One Console](https://docs.nginx.com/nginx-one/)
- [NGINX Plus](https://docs.nginx.com/nginx/) R31+
- [NGINX App Protect WAF](https://docs.nginx.com/nginx-app-protect-waf/) v4 or v5 with precompiled [policy bundles](https://docs.nginx.com/nginx-app-protect-waf/v5/admin-guide/compiler/)

The JSON schema is self explanatory. See also the [sample Postman collection](/contrib/postman) for usage examples

- `.output.license` defines the JWT license to use for NGINX Plus R33+
  - `.output.license.endpoint` the usage reporting endpoint (defaults to `product.connect.nginx.com`). NGINX Instance Manager address can be used here
  - `.output.license.token` the JWT license token. If this field is omitted, it is assumed that a `/etc/nginx/license.jwt` token already exists on the instance and it won't be replaced
  - `.output.license.ssl_verify` set to `false` to trust all SSL certificates (not recommended). Useful for reporting to NGINX Instance Manager without a local PKI.
  - `.output.license.grace_period` Set to 'true' to begin the 180-day reporting enforcement grace period. Reporting must begin or resume before the end of the grace period to ensure continued operation
- `.output.type` defines how NGINX configuration will be returned:
  - *nms* - NGINX configuration is published as a Staged Config to NGINX Instance Manager
    - `.output.nms.url` the NGINX Instance Manager URL
    - `.output.nms.username` the NGINX Instance Manager authentication username
    - `.output.nms.password` the NGINX Instance Manager authentication password
    - `.output.nms.instancegroup` the NGINX Instance Manager instance group to publish the configuration to
    - `.output.nms.synctime` **optional**, used for GitOps autosync. When specified and the declaration includes HTTP(S) references to NGINX App Protect policies, TLS certificates/keys/chains, the HTTP(S) endpoints will be checked every `synctime` seconds and if external contents have changed, the updated configuration will automatically be published to NGINX Instance Manager
    - `.output.nms.synchronous` **optional**, when set to `True` (default) the NGINX Declarative API waits for NGINX Instance Manager successful reply after publishing the NGINX configuration. Setting this to `False` enqueues the request, supporting multiple JSON declaration to be submitted at the same time/from multiple clients
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
  - *nginxone* - NGINX configuration is published to a NGINX One Console config sync group
    - `.output.nginxone.url` the NGINX One Console URL
    - `.output.nginxone.namespace` the NGINX One Console namespace
    - `.output.nginxone.token` the authentication token
    - `.output.nginxone.configsyncgroup` the NGINX One Console config sync group name
    - `.output.nginxone.synctime` **optional**, used for GitOps autosync. When specified and the declaration includes HTTP(S) references to NGINX App Protect policies, TLS certificates/keys/chains, the HTTP(S) endpoints will be checked every `synctime` seconds and if external contents have changed, the updated configuration will automatically be published to NGINX One Cloud Console
    - `.output.nms.synchronous` **optional**, when set to `True` (default) the NGINX Declarative API waits for NGINX One Console successful reply after publishing the NGINX configuration. Setting this to `False` enqueues the request, supporting multiple JSON declaration to be submitted at the same time/from multiple clients
    - `.output.nginxone.modules` an optional array of NGINX module names (ie. 'ngx_http_app_protect_module', 'ngx_http_js_module','ngx_stream_js_module')
    - `.output.nginxone.certificates` an optional array of TLS certificates/keys/chains to be published
      - `.output.nginxone.certificates[].type` the item type ('certificate', 'key', 'chain')
      - `.output.nginxone.certificates[].name` the certificate/key/chain name with no path/extension (ie. 'test-application')
      - `.output.nginxone.certificates[].contents` the content: this can be either base64-encoded or be a HTTP(S) URL that will be fetched dynamically from a source of truth
- `.declaration` describes the NGINX configuration to be created
  - `.declaration.http[]` NGINX HTTP definitions
  - `.declaration.layer4[]` NGINX TCP/UDP definitions
  - `.declaration.resolvers[]` DNS resolvers definitions

### API endpoints

- `POST /v5.3/config/` - Publish a new declaration
- `PATCH /v5.3/config/{config_uid}` - Update an existing declaration
  - Per-HTTP server CRUD
  - Per-HTTP upstream CRUD
  - Per-Stream server CRUD
  - Per-Stream upstream CRUD
  - Per-NGINX App Protect WAF policy CRUD
- `GET /v5.3/config/{configUid}/submission/{submissionUid}` - Retrieve a submission (asynchronous `PATCH` request) status
- `GET /v5.3/config/{config_uid}` - Retrieve an existing declaration
- `DELETE /v5.3/config/{config_uid}` - Delete an existing declaration