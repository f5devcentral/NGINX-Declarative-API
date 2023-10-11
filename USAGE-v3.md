# Usage for API v2

Version 3 API requires:
- NGINX Instance Manager 2.10.0+
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
    - `.output.nms.url` the NMS URL
    - `.output.nms.username` the NMS authentication username
    - `.output.nms.password` the NMS authentication password
    - `.output.nms.instancegroup` the NMS instance group to publish the configuration to
    - `.output.nms.synctime` **optional**, used for GitOps autosync. When specified and the declaration includes HTTP(S) references to NGINX App Protect policies, TLS certificates/keys/chains, the HTTP(S) endpoints will be checked every `synctime` seconds and if external contents have changed, the updated configuration will automatically be published to NMS
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

### Maps ###

Map entries `.declaration.maps[].entries.keymatch` can be:

- *exact* - exact variable matching
- *regex* - case sensitive regex matching
- *iregex* - case insensitive regex matching


### Snippets ###

Snippets for http, upstream, server and location can be specified as:
- base64-encoded content
- HTTP(S) URL of a source of truth to fetch snippet content from. Content on the source of truth must be plaintext, it will be automatically base64-encoded 

### Methods ###

- `POST /v2/config/` - Publish a new declaration
- `PATCH /v2/config/{config_uid}` - Update an existing declaration
  - Per-HTTP server CRUD
  - Per-HTTP upstream CRUD
  - Per-Stream server CRUD
  - Per-Stream upstream CRUD
  - Per-NGINX App Protect WAF policy CRUD
- `GET /v2/config/{config_uid}` - Retrieve an existing declaration
- `DELETE /v2/config/{config_uid}` - Delete an existing declaration

A sample Postman collection is available [here](/postman)

### Sample declaration ###

A sample declaration (to be POSTed to /v2/config) is:

```
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
                "ngx_http_app_protect_module",
                "ngx_http_js_module",
                "ngx_stream_js_module"
            ],
            "certificates": [
                {
                    "type": "certificate",
                    "name": "test_cert",
                    "contents": "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURSVENDQWkwQ0ZDQUVQMGU3U3A4MlFudE5xZFZOQXB3b1VOeDJNQTBHQ1NxR1NJYjNEUUVCQ3dVQU1GOHgKQ3pBSkJnTlZCQVlUQWtsVU1RNHdEQVlEVlFRSURBVk5hV3hoYmpFT01Bd0dBMVVFQnd3RlRXbHNZVzR4RlRBVApCZ05WQkFvTURGUmxjM1FnUTI5dGNHRnVlVEVaTUJjR0ExVUVBd3dRZEdWemRDNWpiMjF3WVc1NUxteGhZakFlCkZ3MHlNakExTVRZd056VTROVGRhRncwek1qQTFNVE13TnpVNE5UZGFNRjh4Q3pBSkJnTlZCQVlUQWtsVU1RNHcKREFZRFZRUUlEQVZOYVd4aGJqRU9NQXdHQTFVRUJ3d0ZUV2xzWVc0eEZUQVRCZ05WQkFvTURGUmxjM1FnUTI5dApjR0Z1ZVRFWk1CY0dBMVVFQXd3UWRHVnpkQzVqYjIxd1lXNTVMbXhoWWpDQ0FTSXdEUVlKS29aSWh2Y05BUUVCCkJRQURnZ0VQQURDQ0FRb0NnZ0VCQU1kaE02Yy8wdGpzT0lmTTlBMjNzQzJJK0dtZzd3NUJVbWRHQjlNc0pTa0IKZ3BQajZ6OTBHbFc3d0dRc25CQ0NNdmtwTzMzRVY0MWlPa0MzYnU3Ym50NXVkTi9kbEg0ZndnMzYrUWdpMnlTegpuVW5OUUNOQkRJTWNRcmFvcjlKdG5SWDAzYXVpY3ZSeEpGQ2lvL1gvNjNIMUFHZERKaFNWaUxRVjlqVjZhNlpNCjFMNDljUVVwekhSSlpPRGV1MnNIc2kxR0JuLzVnUStXSVR2RFp3SGQ0TjJGTkhmOXlJS1ZVQmkzVVRXQmpRRS8KVm15dkZVcmVBYnlldElzbEcvZVVVRkUyeFFhSzFXS2dMVUJrOXRnc3pycXFkNW11Y25ESmZ1elhkclArc1U2YQpkL1kvZVgxN3RKaG5xa25MZ25mVG91NTVLak9XdE93ZzN4OWt5amQ5bkFNQ0F3RUFBVEFOQmdrcWhraUc5dzBCCkFRc0ZBQU9DQVFFQXhyY1ppemR0L0wxWjVYQnE2R0djWTNSbzB0ZEdjdGZHZ0NsdjRvRzVTaE5BQmRhQTIvQ1YKVkE0TGtkb3JYV09hQWNGaWxpcFBlN0tGYVdIZ3EwZ3Q0eEt4LzlkOVZIcU5OY2srTlk0U3dHNDNrWjMyQWQ0QwpnUlowNEVhc1g3aG5wOG13alpLQ0FIWkpGK2krdC9sSFJOaEFDUzFGMHpyQmMrK3NUek5RK1dnTnVEbzN2OWkyCkNoZ1BRbEtBc3M0enM1NGE1RmJOTDJkWWJqNGRraXhJNDMwbU15dXg4SGJPUWFzVm9DVnpXcWtLa29RN25kdUgKRVBrWU0zRy9yVXRQZzhOVU1VVnlkdDFVbnlkb3c4cnhYYjZiQzYreTFQc2FrWHhSdW10ZFlnbDN3UWtJaitGUAoxVFgwSU9qKzdNZnR0cWdxemFhUm85V0s1Y3dpZTBlRGZBPT0KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo="
                },
                {
                    "type": "key",
                    "name": "test_key",
                    "contents": "LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tCk1JSUV2QUlCQURBTkJna3Foa2lHOXcwQkFRRUZBQVNDQktZd2dnU2lBZ0VBQW9JQkFRREhZVE9uUDlMWTdEaUgKelBRTnQ3QXRpUGhwb084T1FWSm5SZ2ZUTENVcEFZS1Q0K3MvZEJwVnU4QmtMSndRZ2pMNUtUdDl4RmVOWWpwQQp0Mjd1MjU3ZWJuVGYzWlIrSDhJTit2a0lJdHNrczUxSnpVQWpRUXlESEVLMnFLL1NiWjBWOU4ycm9uTDBjU1JRCm9xUDEvK3R4OVFCblF5WVVsWWkwRmZZMWVtdW1UTlMrUFhFRktjeDBTV1RnM3J0ckI3SXRSZ1ovK1lFUGxpRTcKdzJjQjNlRGRoVFIzL2NpQ2xWQVl0MUUxZ1kwQlAxWnNyeFZLM2dHOG5yU0xKUnYzbEZCUk5zVUdpdFZpb0MxQQpaUGJZTE02NnFuZVpybkp3eVg3czEzYXovckZPbW5mMlAzbDllN1NZWjZwSnk0SjMwNkx1ZVNvemxyVHNJTjhmClpNbzNmWndEQWdNQkFBRUNnZ0VBQUljZWhSMERVRlZaa1pudVhTdzJhRnVtM2pGYmcyMEhCNnZkdFgyQzA4ZUYKMUthYjhmQzJFN0kyUTc4ZUhNZ3JQZVZuUmlyclVsWHZieGI4S0dpWkg1b1pwOFgwR1oxU2FqREVOMEg5emUvcwpBSmY4c1daSzJEYkJ0ajRHTmlVazR6djNQeXMwYXVvWWx1TmtJbkpRbDZYNGVLWkIwVjBYbW54NEJpejNGVVVVCjliUlRlM09FTFYwNDVMUkt3eWRnOWFmQnZQcEZIQkdIcVBxRFptTHl6TWVNQjVHVmJBOEd2NVE4QS96WFdtcnoKSVE0QVlZeVU1dlZXKzBya0NRRVluR1c5QlNiYjB6d3prdVBKa1NRODhzOHV0T2RmMU5SOGZBVkdnazhXVHZXagpRVnlKVzV6Snc2SzlsS0w2Sy94VDlKOUZiWWpQWFZDd21jaDMweUpPWVFLQmdRRFI3NmpkRnhzMTZKMXR3U3Z0CkJBRWMzOVFCeTBPNmNQSWJLV1hYOE1FRDB1R0psYUJRSWE5WUdoS3lGYU5SRjJVTUJYWHVZVll1U2Rrb1lxMGwKNVBndmJoNVYxQjFVYVR5WG0rUTlBcWFsc3pSQW5TdXFKcytsVzJDaE5ISDRZQjlnKzQrZFlmcURuMWdTUlkzMgpvZVlrV05aQ0VHT0c0QUNtSTJXZU8wWklyd0tCZ1FEeklKTFRzQnJ3MldlMW8zOVd2RkpIaFF6RDRNU2ppSHovClRSZS9VV2ZEWlB1TzZmcXBHNXozbk9oWkVsUEJuRktKNTZQekZhemxJQ01xdmpoRHZtTkpmb1J3Y084cnVhOG8KenVzb2N0bk15UzFPOExSMDltZFlPdVhyY0RXamZ5QTdlZHBiWUVSTGYzQXJkL2VJZko0RTJ3SGI3bVhMRHgxbApRdnBjR3VsTzdRS0JnREgzK0ZwL2VIT1JaWDlOUGxaUTRLN3R1N21kbHdaV2dkbmpOYUY3WllXeWVRcFZlZTM0CnhwS1N5aVpuTGhOTUhUb0tSckt4cW1Da0pUTU9vYVhtWlFodERuMWhXb1hQOHFNbmNPRHdzNWUzR3RYU1V5VlIKelpUUE5pWElwT1A0aFIrQllRS1Y0cG5Yb0kvZ3pGU0szb3VDTmFWTjMxS29HSjl5eDJvdE02SnpBb0dBTDZicAp3RDNhK2V2U2pPSlB1Z05OS1NGbHdCcVV6K3lYZXo1ejhoYVZmTkdWRUl6QmlWV1ZMVjcrbHo2bFZlUTZ0VGJHCmhvVndEclIrMEFqYVpFU3pseHNLQURQU1hNS1hGeXQvSWIxby9OOU5WeFNNZWdRMWV6Q0lFZDQ3VlNFOGd3dSsKQlh6WHhlaGpadEdyblgrM1JRSmIyZXhlM1M3SU55bXFnbFR2OTMwQ2dZQkpsK2EvRHN0OE5iVlEvRHpuei93VgpPSDhKUENOS05EQm1WS3ZUVTNiQy9YQW8rQm42a2crbDZqczY5RkZlWHIvOGlHL25sTW9QQTlnT2Zxb3BmZ3AzClpTZFE1RlMrQk9kdFQrT2JacTBlcmxJSlk0dW9na3VEV2NpLzNaeExkYnNQUnhJS2c4MmdYRU9DN1dnb3VsUVQKV1doVUpSeGpJdGx6eUdseHhvb2lqQT09Ci0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS0K"
                },
                {
                    "type": "certificate",
                    "name": "cacert",
                    "contents": "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUZjekNDQTF1Z0F3SUJBZ0lVVnNRZkFaTW4vazNRTU9nc0RuVEdUaU9PbGJ3d0RRWUpLb1pJaHZjTkFRRUwKQlFBd1NURUxNQWtHQTFVRUJoTUNTVlF4RFRBTEJnTlZCQWdNQkVGemRHa3hFVEFQQmdOVkJBb01DRlJsYzNRZwpUR0ZpTVJnd0ZnWURWUVFEREE5MmJTMWliR0Z1YXk1bVppNXNZVzR3SGhjTk1qTXdOakE0TURrMU5EQTRXaGNOCk1qUXdOakEzTURrMU5EQTRXakJKTVFzd0NRWURWUVFHRXdKSlZERU5NQXNHQTFVRUNBd0VRWE4wYVRFUk1BOEcKQTFVRUNnd0lWR1Z6ZENCTVlXSXhHREFXQmdOVkJBTU1EM1p0TFdKc1lXNXJMbVptTG14aGJqQ0NBaUl3RFFZSgpLb1pJaHZjTkFRRUJCUUFEZ2dJUEFEQ0NBZ29DZ2dJQkFLMlQwWXpkcjB0dWQzaVJRNGNzaGNhRVJTRzVjTDE2CkhRblhoYWw4emlUL1VRQUNIUGdzZDYwcWlEaldvQTJXb0lGWFFpUHkzOG1vZGtWRlR4Qmt5U2VldndOOFJiLzEKOFhaMS8yS1RnVmRDcHkvNm11WE15bXZYODJad05CVkV3QnoxUk5kbklUSk44cVh3a0d4bHozbDBib1loRkFyUQpNdmkxcW1RaHpDa2Zpb041MVkrYlBXOXpTQlFQdXNrcXJYYzRqTTJ0VENNQ2pTcFlvd1hXM1ppRmc5WEJ1Z09aCjFmdWd1Zmw4K1FJYzNZSEFoL1Z1NloraXFEOGxQeGRKODlBeDZaazVtOGdkVG9JdUhBbUNWaHFpUXBGRjkzSTgKbkYrSnRuYnBaNTRJUTZBbWYrYiswakMxdmY4Kzg0WUppaEVzWExyaGMxZTRTZ2dwdzEvcWpDb21QblhGVjEzUwpsUG5kVlhVR0taa1ZKdXdZTjJyZElmd3YrdCs5MGhwUVBmNmFBTjRCamRxOXdkdkQzSXVnS2JYZG5CQ0FUTEY4ClYyRTFTSE9VZGdRY3duK1d1WDVVOGdPa3B2b2VFN0g1REJ6Rks1WTZ2SHZlaTRlNkp3RTRDK3FJL1BmbTgreTEKNEpsOFBSOW5JQmdGQ3hrZWpwa2tRQ0I5U0dvMVZidzZhWmdZd0VQNHh6YXFYYXV3L3F4c0oxNUkrRTBndEs1OApuWUtkM0hqelk5Slh6V0NVNTdXbmc2SzNvTTIzNXpyRzJnNm1FaHQ4SStDckVMUFNuZURjZU8zVlJkc2dlblBCCis4U1JxVU8vWG9LWHNEU3I5amoxdWluVzYwTG5MZ0Zmc3JQeGlQVlZlMFh1TFZESlhCSlNoRDZDeGRyMnBSOGQKS25SRDZrTFpZZEtMQWdNQkFBR2pVekJSTUIwR0ExVWREZ1FXQkJRUzZnS2pMK3VFc0dXeXVjbTZyb0xVaXpqVwpWREFmQmdOVkhTTUVHREFXZ0JRUzZnS2pMK3VFc0dXeXVjbTZyb0xVaXpqV1ZEQVBCZ05WSFJNQkFmOEVCVEFECkFRSC9NQTBHQ1NxR1NJYjNEUUVCQ3dVQUE0SUNBUUJad3B4Z2Z4N2thZFhvRHNyT1hUVXJ6dEFPMkFQRVJNaTAKaTkyNk9DTGFPbVVYZW1uKytXSUU1K2tUSE0wcS8vbUZCTURzSmdZSFVLUlNvRGNsNmh4TnVFNUNzS2trRVFTSgpMTHZrWlB0S2J5NGlxMitLZ1JtdVZxbXJNVTBYQzZMZDl3WmttL2huUjNtT3V6bko4MGZmV1JDQ0xGWDEwY2EzCnc5TGM1d1JLTFBZZXQvcEs5SitOYWN3TFJRYTczVFovMUpQNW9BU3czVjNoYkxlLy9UeWpnOURqUlZGY3FYWnEKWWs2Mm5qSkhZVzh3WmlhZzc0QXU4dHE5OG5KandBV1ROMFV5L2w1Q2VpWnV5bzZlU0RHVDNJNm1BdGU1VXBvWAppNXBkYlZ6VDdOZC9IOEwwZHZNdVZ2N0FmakZlcU91cUZNNkkzTnlvbStLWENxNmJQdGxBWEkzeVFZc0t4ZlRkCkw3SnRaTmx6MGJ6eHJhcHI4RmpYcjhML1ZkeHQza00xMnJwb2kzL3hsckR6Q2Q2b2YrQ1MxelBocUdpOUhvcUoKZEU5VGhYMklTdkd2akVSYzVVNFRsNjJBNHNyeGJQbUt0eWx3dGNGVEJacUJiRGY3ZjBBc2cveWhndXdTcktsQQpBNkRWVXVCRFErdGpwZ0N0b0ZlOEhLVDJ6UFVlaEQ2ZjVNQkhmU2ZUZ1crTlhFSXNvVDNsampjY1hsYXhPcFJWCkNQNWxCczNmekxyYnBxbUlLaWZhdWlTNWM4TzlSUjhjQTVzeWlBOTBmbmJIdDlmdGxpRG9jcFRzNUtrbjk2NkIKZUxMM1dXVldCYUtvanJzY1RkVXJoalNnVVBmam5FTXpnVzR2eEc3d3BVNHR2ME4yaEtHUWc0bVhhcDV0SU5Pcwp4WktnZXRHUldnPT0KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo="
                }
            ],
            "policies": [
                {
                    "type": "app_protect",
                    "name": "prod-policy",
                    "active_tag": "v1",
                    "versions": [
                        {
                            "tag": "v1",
                            "displayName": "Production Policy - blocking",
                            "description": "Production-ready policy - blocking",
                            "contents": "ewogICAgInBvbGljeSI6IHsKICAgICAgICAibmFtZSI6ICJwcm9kLXBvbGljeSIsCiAgICAgICAgInRlbXBsYXRlIjogewogICAgICAgICAgICAibmFtZSI6ICJQT0xJQ1lfVEVNUExBVEVfTkdJTlhfQkFTRSIKICAgICAgICB9LAogICAgICAgICJhcHBsaWNhdGlvbkxhbmd1YWdlIjogInV0Zi04IiwKICAgICAgICAiZW5mb3JjZW1lbnRNb2RlIjogImJsb2NraW5nIiwKICAgICAgICAic2lnbmF0dXJlLXNldHMiOiBbCiAgICAgICAgICAgIHsKICAgICAgICAgICAgICAgICJuYW1lIjogIkFsbCBTaWduYXR1cmVzIiwKICAgICAgICAgICAgICAgICJibG9jayI6IHRydWUsCiAgICAgICAgICAgICAgICAiYWxhcm0iOiB0cnVlCiAgICAgICAgICAgIH0KICAgICAgICBdLAogICAgICAgICJzaWduYXR1cmVzIjogWwogICAgICAgICAgICB7CiAgICAgICAgICAgICAgICAic2lnbmF0dXJlSWQiOiAyMDAwMDE4MzQsCiAgICAgICAgICAgICAgICAiZW5hYmxlZCI6IGZhbHNlCiAgICAgICAgICAgIH0KICAgICAgICBdCiAgICB9Cn0K"
                        },
                        {
                            "tag": "v2",
                            "displayName": "Production Policy - XSS allowed",
                            "description": "Production-ready policy - XSS allowed",
                            "contents": "ewogICAgInBvbGljeSI6IHsKICAgICAgICAibmFtZSI6ICJwcm9kLXBvbGljeSIsCiAgICAgICAgInRlbXBsYXRlIjogewogICAgICAgICAgICAibmFtZSI6ICJQT0xJQ1lfVEVNUExBVEVfTkdJTlhfQkFTRSIKICAgICAgICB9LAogICAgICAgICJhcHBsaWNhdGlvbkxhbmd1YWdlIjogInV0Zi04IiwKICAgICAgICAiZW5mb3JjZW1lbnRNb2RlIjogImJsb2NraW5nIiwKICAgICAgICAic2lnbmF0dXJlLXNldHMiOiBbCiAgICAgICAgICAgIHsKICAgICAgICAgICAgICAgICJuYW1lIjogIkFsbCBTaWduYXR1cmVzIiwKICAgICAgICAgICAgICAgICJibG9jayI6IHRydWUsCiAgICAgICAgICAgICAgICAiYWxhcm0iOiB0cnVlCiAgICAgICAgICAgIH0KICAgICAgICBdLAogICAgICAgICJzaWduYXR1cmVzIjogWwogICAgICAgICAgICB7CiAgICAgICAgICAgICAgICAic2lnbmF0dXJlSWQiOiAyMDAwMDE4MzQsCiAgICAgICAgICAgICAgICAiZW5hYmxlZCI6IGZhbHNlCiAgICAgICAgICAgIH0sCiAgICAgICAgICAgIHsKICAgICAgICAgICAgICAgICJzaWduYXR1cmVJZCI6IDIwMDAwMTQ3NSwKICAgICAgICAgICAgICAgICJlbmFibGVkIjogZmFsc2UKICAgICAgICAgICAgfSwKICAgICAgICAgICAgewogICAgICAgICAgICAgICAgInNpZ25hdHVyZUlkIjogMjAwMDAwMDk4LAogICAgICAgICAgICAgICAgImVuYWJsZWQiOiBmYWxzZQogICAgICAgICAgICB9LAogICAgICAgICAgICB7CiAgICAgICAgICAgICAgICAic2lnbmF0dXJlSWQiOiAyMDAwMDEwODgsCiAgICAgICAgICAgICAgICAiZW5hYmxlZCI6IGZhbHNlCiAgICAgICAgICAgIH0sCiAgICAgICAgICAgIHsKICAgICAgICAgICAgICAgICJzaWduYXR1cmVJZCI6IDIwMDEwMTYwOSwKICAgICAgICAgICAgICAgICJlbmFibGVkIjogZmFsc2UKICAgICAgICAgICAgfQogICAgICAgIF0KICAgIH0KfQo="
                        }
                    ]
                }
            ]
        }
    },
    "declaration": {
        "layer4": {
            "servers": [
                {
                    "name": "sample_layer4_service",
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
                    "name": "HTTP test application",
                    "names": [
                        "server_8080.nginx.lab",
                        "server_8081.nginx.lab"
                    ],
                    "resolver": "8.8.8.8",
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
                            "snippet": "http://acme.gitlab.local/test.snippet.location.txt"
                        }
                    ],
                    "app_protect": {
                        "enabled": true,
                        "policy": "prod-policy",
                        "log": {
                            "profile_name": "log_blocked",
                            "enabled": true,
                            "destination": "192.168.1.5:514"
                        }
                    },
                    "snippet": "IyBUaGlzIGlzIGEgc2VydmVyIHNuaXBwZXQgY29tbWVudAo="
                },
                {
                    "name": "another HTTP test application",
                    "names": [
                        "server_443"
                    ],
                    "resolver": "8.8.8.8",
                    "listen": {
                        "address": "0.0.0.0:443",
                        "http2": true,
                        "tls": {
                            "certificate": "test_cert",
                            "key": "test_key",
                            "trusted_ca_certificates": "cacert",
                            "ciphers": "DEFAULT",
                            "protocols": [
                                "TLSv1.2",
                                "TLSv1.3"
                            ],
                            "mtls": {
                                "enabled": "on",
                                "client_certificates": "cacert"
                            },
                            "ocsp": {
                                "enabled": "on",
                                "responder": "http://ocsp.mylab.lan"
                            },
                            "stapling": {
                                "enabled": true,
                                "verify": true,
                                "responder": "http://ocsp.mylab.lan"
                            }
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
