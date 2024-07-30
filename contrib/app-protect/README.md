# REST API for NGINX App Protect WAF Compiler

This contrib provides a set of REST API to use the NGINX App Protect 5 policy compiler

## REST API Endpoints

- `/v1/compile/policy` - compiles a JSON policy into a bundle
  - Method: `POST`
  - Payload: `{"global-settings": "<BASE64_ENCODED_GLOBAL_SETTINGS_JSON>", "policy": "<BASE64_ENCODED_POLICY_JSON>"}`
- `/v1/compile/logprofile` - compiles a log profile JSON into a bundle
  - Method: `POST`
  - Payload: `{"logprofile": "<BASE64_ENCODED_LOG_PROFILE_JSON>"}`
- `/v1/bundle/info` - returns details on a compiled bundle
  - Method: `POST`
  - Payload: `{"bundle": "<BASE64_ENCODED_TGZ_BUNDLE>"}`

Headers required for all endpoints:

```
Content-Type: application/json
```