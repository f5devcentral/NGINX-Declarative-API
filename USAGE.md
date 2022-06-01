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

All snippets must be base64-encoded


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
                    "type": "chain",
                    "name": "test_chain",
                    "contents": "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURSVENDQWkwQ0ZDQUVQMGU3U3A4MlFudE5xZFZOQXB3b1VOeDJNQTBHQ1NxR1NJYjNEUUVCQ3dVQU1GOHgKQ3pBSkJnTlZCQVlUQWtsVU1RNHdEQVlEVlFRSURBVk5hV3hoYmpFT01Bd0dBMVVFQnd3RlRXbHNZVzR4RlRBVApCZ05WQkFvTURGUmxjM1FnUTI5dGNHRnVlVEVaTUJjR0ExVUVBd3dRZEdWemRDNWpiMjF3WVc1NUxteGhZakFlCkZ3MHlNakExTVRZd056VTROVGRhRncwek1qQTFNVE13TnpVNE5UZGFNRjh4Q3pBSkJnTlZCQVlUQWtsVU1RNHcKREFZRFZRUUlEQVZOYVd4aGJqRU9NQXdHQTFVRUJ3d0ZUV2xzWVc0eEZUQVRCZ05WQkFvTURGUmxjM1FnUTI5dApjR0Z1ZVRFWk1CY0dBMVVFQXd3UWRHVnpkQzVqYjIxd1lXNTVMbXhoWWpDQ0FTSXdEUVlKS29aSWh2Y05BUUVCCkJRQURnZ0VQQURDQ0FRb0NnZ0VCQU1kaE02Yy8wdGpzT0lmTTlBMjNzQzJJK0dtZzd3NUJVbWRHQjlNc0pTa0IKZ3BQajZ6OTBHbFc3d0dRc25CQ0NNdmtwTzMzRVY0MWlPa0MzYnU3Ym50NXVkTi9kbEg0ZndnMzYrUWdpMnlTegpuVW5OUUNOQkRJTWNRcmFvcjlKdG5SWDAzYXVpY3ZSeEpGQ2lvL1gvNjNIMUFHZERKaFNWaUxRVjlqVjZhNlpNCjFMNDljUVVwekhSSlpPRGV1MnNIc2kxR0JuLzVnUStXSVR2RFp3SGQ0TjJGTkhmOXlJS1ZVQmkzVVRXQmpRRS8KVm15dkZVcmVBYnlldElzbEcvZVVVRkUyeFFhSzFXS2dMVUJrOXRnc3pycXFkNW11Y25ESmZ1elhkclArc1U2YQpkL1kvZVgxN3RKaG5xa25MZ25mVG91NTVLak9XdE93ZzN4OWt5amQ5bkFNQ0F3RUFBVEFOQmdrcWhraUc5dzBCCkFRc0ZBQU9DQVFFQXhyY1ppemR0L0wxWjVYQnE2R0djWTNSbzB0ZEdjdGZHZ0NsdjRvRzVTaE5BQmRhQTIvQ1YKVkE0TGtkb3JYV09hQWNGaWxpcFBlN0tGYVdIZ3EwZ3Q0eEt4LzlkOVZIcU5OY2srTlk0U3dHNDNrWjMyQWQ0QwpnUlowNEVhc1g3aG5wOG13alpLQ0FIWkpGK2krdC9sSFJOaEFDUzFGMHpyQmMrK3NUek5RK1dnTnVEbzN2OWkyCkNoZ1BRbEtBc3M0enM1NGE1RmJOTDJkWWJqNGRraXhJNDMwbU15dXg4SGJPUWFzVm9DVnpXcWtLa29RN25kdUgKRVBrWU0zRy9yVXRQZzhOVU1VVnlkdDFVbnlkb3c4cnhYYjZiQzYreTFQc2FrWHhSdW10ZFlnbDN3UWtJaitGUAoxVFgwSU9qKzdNZnR0cWdxemFhUm85V0s1Y3dpZTBlRGZBPT0KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo="
                }
            ],
            "policies": [
                {
                    "type": "app_protect",
                    "name": "test_policy",
                    "contents": "eyJwb2xpY3kiOnsiYXBwbGljYXRpb25MYW5ndWFnZSI6InV0Zi04IiwiYmxvY2tpbmctc2V0dGluZ3MiOnsiZXZhc2lvbnMiOlt7ImRlc2NyaXB0aW9uIjoiQXBhY2hlIHdoaXRlc3BhY2UiLCJlbmFibGVkIjp0cnVlfSx7ImRlc2NyaXB0aW9uIjoiQmFkIHVuZXNjYXBlIiwiZW5hYmxlZCI6dHJ1ZX0seyJkZXNjcmlwdGlvbiI6IkJhcmUgYnl0ZSBkZWNvZGluZyIsImVuYWJsZWQiOnRydWV9LHsiZGVzY3JpcHRpb24iOiJEaXJlY3RvcnkgdHJhdmVyc2FscyIsImVuYWJsZWQiOnRydWV9LHsiZGVzY3JpcHRpb24iOiJJSVMgVW5pY29kZSBjb2RlcG9pbnRzIiwiZW5hYmxlZCI6dHJ1ZX0seyJkZXNjcmlwdGlvbiI6IklJUyBiYWNrc2xhc2hlcyIsImVuYWJsZWQiOnRydWV9LHsiZGVzY3JpcHRpb24iOiJNdWx0aXBsZSBkZWNvZGluZyIsImVuYWJsZWQiOnRydWUsIm1heERlY29kaW5nUGFzc2VzIjoyfV0sImh0dHAtcHJvdG9jb2xzIjpbeyJkZXNjcmlwdGlvbiI6IkhlYWRlciBuYW1lIHdpdGggbm8gaGVhZGVyIHZhbHVlIiwiZW5hYmxlZCI6dHJ1ZX1dLCJ2aW9sYXRpb25zIjpbeyJhbGFybSI6dHJ1ZSwiYmxvY2siOmZhbHNlLCJuYW1lIjoiVklPTF9EQVRBX0dVQVJEIn0seyJhbGFybSI6dHJ1ZSwiYmxvY2siOnRydWUsIm5hbWUiOiJWSU9MX0hUVFBfUFJPVE9DT0wifSx7ImFsYXJtIjp0cnVlLCJibG9jayI6dHJ1ZSwibmFtZSI6IlZJT0xfRklMRVRZUEUifSx7ImFsYXJtIjp0cnVlLCJibG9jayI6dHJ1ZSwibmFtZSI6IlZJT0xfSEVBREVSX01FVEFDSEFSIn0seyJhbGFybSI6dHJ1ZSwiYmxvY2siOnRydWUsIm5hbWUiOiJWSU9MX0VWQVNJT04ifV19LCJkYXRhLWd1YXJkIjp7ImNyZWRpdENhcmROdW1iZXJzIjp0cnVlLCJlbmFibGVkIjp0cnVlLCJlbmZvcmNlbWVudE1vZGUiOiJpZ25vcmUtdXJscy1pbi1saXN0IiwiZW5mb3JjZW1lbnRVcmxzIjpbXSwibWFza0RhdGEiOnRydWUsInVzU29jaWFsU2VjdXJpdHlOdW1iZXJzIjp0cnVlfSwiZW5mb3JjZW1lbnRNb2RlIjoiYmxvY2tpbmciLCJmaWxldHlwZXMiOlt7ImFsbG93ZWQiOnRydWUsImNoZWNrUG9zdERhdGFMZW5ndGgiOmZhbHNlLCJjaGVja1F1ZXJ5U3RyaW5nTGVuZ3RoIjp0cnVlLCJjaGVja1JlcXVlc3RMZW5ndGgiOmZhbHNlLCJjaGVja1VybExlbmd0aCI6dHJ1ZSwibmFtZSI6IioiLCJwb3N0RGF0YUxlbmd0aCI6NDA5NiwicXVlcnlTdHJpbmdMZW5ndGgiOjIwNDgsInJlcXVlc3RMZW5ndGgiOjgxOTIsInJlc3BvbnNlQ2hlY2siOmZhbHNlLCJ0eXBlIjoid2lsZGNhcmQiLCJ1cmxMZW5ndGgiOjIwNDh9LHsiYWxsb3dlZCI6ZmFsc2UsIm5hbWUiOiJiYXQifV0sImdlbmVyYWwiOnsidHJ1c3RYZmYiOnRydWV9LCJuYW1lIjoibmdpbngtcG9saWN5Iiwic2lnbmF0dXJlLXNldHMiOlt7ImFsYXJtIjp0cnVlLCJibG9jayI6dHJ1ZSwibmFtZSI6IkNvbW1hbmQgRXhlY3V0aW9uIFNpZ25hdHVyZXMifSx7ImFsYXJtIjp0cnVlLCJibG9jayI6dHJ1ZSwibmFtZSI6IkNyb3NzIFNpdGUgU2NyaXB0aW5nIFNpZ25hdHVyZXMifSx7ImFsYXJtIjp0cnVlLCJibG9jayI6dHJ1ZSwibmFtZSI6IlNRTCBJbmplY3Rpb24gU2lnbmF0dXJlcyJ9XSwic2lnbmF0dXJlLXNldHRpbmdzIjp7Im1pbmltdW1BY2N1cmFjeUZvckF1dG9BZGRlZFNpZ25hdHVyZXMiOiJsb3cifSwidGVtcGxhdGUiOnsibmFtZSI6IlBPTElDWV9URU1QTEFURV9OR0lOWF9CQVNFIn19fQo="
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
