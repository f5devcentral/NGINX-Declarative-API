# Usage for NGINX Declarative API v5.2

Version 5.2 supports:

- [NGINX Instance Manager](https://docs.nginx.com/nginx-management-suite/nim/) 2.18+
- [NGINX One Console](https://docs.nginx.com/nginx-one/)
- [NGINX Plus](https://docs.nginx.com/nginx/) R31, R32, R33+
- [NGINX App Protect WAF](https://docs.nginx.com/nginx-app-protect-waf/) 4 with precompiled [policy bundles](https://docs.nginx.com/nginx-app-protect-waf/v5/admin-guide/compiler/)

The JSON schema is self explanatory. See also the [sample Postman collection](/contrib/postman) for usage examples

- `.output.type` defines how NGINX configuration will be returned:
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
  - *nginxone* - NGINX configuration is published to a NGINX One Console config sync group
    - `.output.nginxone.url` the NGINX One Console URL
    - `.output.nginxone.namespace` the NGINX One Console namespace
    - `.output.nginxone.token` the authentication token
    - `.output.nginxone.configsyncgroup` the NGINX One Console config sync group name
    - `.output.nginxone.synctime` **optional**, used for GitOps autosync. When specified and the declaration includes HTTP(S) references to NGINX App Protect policies, TLS certificates/keys/chains, the HTTP(S) endpoints will be checked every `synctime` seconds and if external contents have changed, the updated configuration will automatically be published to NGINX One Cloud Console
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

- `POST /v5.2/config/` - Publish a new declaration
- `PATCH /v5.2/config/{config_uid}` - Update an existing declaration
  - Per-HTTP server CRUD
  - Per-HTTP upstream CRUD
  - Per-Stream server CRUD
  - Per-Stream upstream CRUD
  - Per-NGINX App Protect WAF policy CRUD
- `GET /v5.2/config/{config_uid}` - Retrieve an existing declaration
- `DELETE /v5.2/config/{config_uid}` - Delete an existing declaration