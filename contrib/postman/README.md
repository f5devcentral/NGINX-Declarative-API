# Sample Postman Collection

This collection contains:

API v4.1 - Latest
- `Configuration generation` - Declaration examples with output to plaintext, JSON, Kubernetes ConfigMap, HTTP POST
- `Declarative automation examples` - Several examples and use cases
  - `API Gateway` - Sample API gateway requests for Swagger and OpenAPI schemas import
  - `CRUD automation` - Sample requests for CRUD-based automation
  - `GitOps autosync` - GitOps automation demo
  - `Housekeeping - common endpoints` - Miscellaneous general purpose requests
  - `JWT Client Authentication` - JWT-based client authentication for HTTP
  - `mTLS Client Authentication` - mTLS client authentication for HTTP
  - `NGINX App Protect WAF` - Sample requests for declarative configuration lifecycle management
  - `Server-side and source of truth authentication` - Requests for authentication towards upstreams and source of truth

API v4.0
- `Configuration generation` - Declaration examples with output to plaintext, JSON, Kubernetes ConfigMap, HTTP POST
- `Declarative automation examples` - Several examples and use cases
  - `API Gateway` - Sample API gateway requests for Swagger and OpenAPI schemas import
  - `CRUD automation` - Sample requests for CRUD-based automation
  - `GitOps autosync` - GitOps automation demo
  - `Housekeeping - common endpoints` - Miscellaneous general purpose requests
  - `JWT Client Authentication` - JWT-based client authentication for HTTP
  - `mTLS Client Authentication` - mTLS client authentication for HTTP
  - `NGINX App Protect WAF` - Sample requests for declarative configuration lifecycle management

API v3.1 - Deprecated
- `Configuration generation` - Declaration examples with output to plaintext, JSON, Kubernetes ConfigMap, HTTP POST
- `Declarative automation - NGINX App Protect WAF` - Sample requests for declarative configuration lifecycle management
- `Declarative automation - GitOps` - GitOps automation demo
- `CRUD automation` - Sample requests for CRUD-based automation
- `API Gateway` - Sample API gateway requests for Swagger and OpenAPI schemas import
- `Examples` - Additional declaration examples
- `Erase configuration` - Erase NGINX Plus configuration

---

## API Gateway ##

Test requests for the `API Gateway` folder in the Postman collection are:

### Petstore ###

Valid request:

    curl -sH "Host: apigw.nginx.lab" http://<NGINX_INSTANCE_IP_ADDRESS>/petstore/store/inventory | jq

Invalid method:

    curl -sH "Host: apigw.nginx.lab" http://<NGINX_INSTANCE_IP_ADDRESS>/petstore/store/inventory -X POST

### Ergast ###

Valid request:

    curl -sH "Host: apigw.nginx.lab" http://<NGINX_INSTANCE_IP_ADDRESS>/ergast/2023.json | jq

Invalid request:

    curl -sH "Host: apigw.nginx.lab" http://<NGINX_INSTANCE_IP_ADDRESS>/ergast/2023.json -X POST


---

**Note**: The `GitOps autosync` folder requires either
- an NGINX instance (OSS or Plus) reachable as `acme.gitlab.local` on port `80/TCP` using the sample configuration available here: [/contrib/sample-source-of-truth/ncg-nginx.conf](/contrib/sample-source-of-truth/ncg-nginx.conf)
- access to the GitHub repository at https://github.com/f5devcentral/NGINX-Declarative-API/ to fetch files under https://github.com/f5devcentral/NGINX-Declarative-API/tree/main/contrib/gitops-examples/v4.0
