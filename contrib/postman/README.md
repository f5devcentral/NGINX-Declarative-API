# Sample Postman Collection

This collection contains:

API v3
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

**Note**: The `GitOps` folder requires either
- an NGINX instance (OSS or Plus) reachable as `acme.gitlab.local` on port `80/TCP` using the sample configuration available here: [/contrib/sample-source-of-truth/ncg-nginx.conf](/contrib/sample-source-of-truth/ncg-nginx.conf)
- access to the GitHub repository at https://github.com/fabriziofiorucci/NGINX-Declarative-API/ to fetch files under https://github.com/fabriziofiorucci/NGINX-Declarative-API/tree/main/contrib/sample-source-of-truth/configs
