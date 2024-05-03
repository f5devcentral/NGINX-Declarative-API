# Sample Postman Collection

This collection contains:

API v4.2 - Latest
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

API v4.1
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

---

## API Gateway ##

Test requests for the `API Gateway` folder in the Postman collection require `apigw.nginx.lab` to resolve to the NGINX instance IP address.

### Petstore ###

Successful request

```
curl -w '\n' -ik https://apigw.nginx.lab/petstore/store/inventory
```

Authentication failed:

```
curl -w '\n' -ik https://apigw.nginx.lab/petstore/user/login 
```

Authentication successful:

```
curl -w '\n' -ik https://apigw.nginx.lab/petstore/user/login -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImtpZCI6IjAwMDEiLCJpc3MiOiJCYXNoIEpXVCBHZW5lcmF0b3IiLCJpYXQiOjE3MDI0ODEzNjcsImV4cCI6MTcwMjQ4MTM2OH0.eyJuYW1lIjoiQm9iIERldk9wcyIsInN1YiI6IkpXVCBzdWIgY2xhaW0iLCJpc3MiOiJKV1QgaXNzIGNsYWltIiwicm9sZXMiOlsiZGV2b3BzIl19.SKA_7MszAypMEtX5NDQ0TcUbVYx_Wt0hrtmuyTmrVKU"
```

Authorization failed (based on JWT `role` claim):

```
curl -w '\n' -ki https://apigw.nginx.lab/petstore/user/login -H "Authorization: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImtpZCI6IjAwMDEiLCJpc3MiOiJCYXNoIEpXVCBHZW5lcmF0b3IiLCJpYXQiOjE3MDk3NjQ3NTMsImV4cCI6MTcwOTc2NDc1NH0.eyJuYW1lIjoiQWxpY2UgR3Vlc3QiLCJzdWIiOiJKV1Qgc3ViIGNsYWltIiwiaXNzIjoiSldUIGlzcyBjbGFpbSIsInJvbGVzIjpbImd1ZXN0Il19.jFJDq-33irz7uFxdI8c8fIb5TwTAU5BlemmIFVALUAE"
```
```
curl -w '\n' -ki https://apigw.nginx.lab/petstore/pet/1/uploadImage -X POST \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImtpZCI6IjAwMDEiLCJpc3MiOiJCYXNoIEpXVCBHZW5lcmF0b3IiLCJpYXQiOjE3MDk3NjQ3NTMsImV4cCI6MTcwOTc2NDc1NH0.eyJuYW1lIjoiQWxpY2UgR3Vlc3QiLCJzdWIiOiJKV1Qgc3ViIGNsYWltIiwiaXNzIjoiSldUIGlzcyBjbGFpbSIsInJvbGVzIjpbImd1ZXN0Il19.jFJDq-33irz7uFxdI8c8fIb5TwTAU5BlemmIFVALUAE" \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AcxV9TS0UqChYRcchQXbSLijjWKhShQqgVWnUwuX5Ck4YkxcVRcC04+LFYdXBx1tXBVRAEP0CcHZwUXaTE/yWFFjEeHPfj3b3H3TtAaFSYanbFAFWzjFQiLmayq2LwFQEI6Mc4BmVm6nOSlITn+LqHj693UZ7lfe7P0ZvLmwzwicQxphsW8QbxzKalc94nDrOSnCM+J54w6ILEj1xXXH7jXHRY4JlhI52aJw4Ti8UOVjqYlQyVeJo4klM1yhcyLuc4b3FWKzXWuid/YSivrSxzneYIEljEEiSIUFBDGRVYiNKqkWIiRftxD/+w45fIpZCrDEaOBVShQnb84H/wu1uzMDXpJoXiQODFtj9GgeAu0Kzb9vexbTdPAP8zcKW1/dUGMPtJer2tRY6Avm3g4rqtKXvA5Q4w9KTLhuxIfppCoQC8n9E3ZYGBW6Bnze2ttY/TByBNXSVvgINDYKxI2ese7+7u7O3fM63+fgB5bXKpzZcBIwAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+gFAhArKAvJglcAAAAZdEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIEdJTVBXgQ4XAAAADElEQVQI12P4//8/AAX+Av7czFnnAAAAAElFTkSuQmCC;type=image/png'
```

Authorization successful (based on JWT `role` claim):

```
curl -w '\n' -ki https://apigw.nginx.lab/petstore/user/login -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImtpZCI6IjAwMDEiLCJpc3MiOiJCYXNoIEpXVCBHZW5lcmF0b3IiLCJpYXQiOjE3MDI0ODEzNjcsImV4cCI6MTcwMjQ4MTM2OH0.eyJuYW1lIjoiQm9iIERldk9wcyIsInN1YiI6IkpXVCBzdWIgY2xhaW0iLCJpc3MiOiJKV1QgaXNzIGNsYWltIiwicm9sZXMiOlsiZGV2b3BzIl19.SKA_7MszAypMEtX5NDQ0TcUbVYx_Wt0hrtmuyTmrVKU"
```

```
curl -w '\n' -ki https://apigw.nginx.lab/petstore/pet/1/uploadImage -X POST \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImtpZCI6IjAwMDEiLCJpc3MiOiJCYXNoIEpXVCBHZW5lcmF0b3IiLCJpYXQiOjE3MDI0ODEzNjcsImV4cCI6MTcwMjQ4MTM2OH0.eyJuYW1lIjoiQm9iIERldk9wcyIsInN1YiI6IkpXVCBzdWIgY2xhaW0iLCJpc3MiOiJKV1QgaXNzIGNsYWltIiwicm9sZXMiOlsiZGV2b3BzIl19.SKA_7MszAypMEtX5NDQ0TcUbVYx_Wt0hrtmuyTmrVKU" \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AcxV9TS0UqChYRcchQXbSLijjWKhShQqgVWnUwuX5Ck4YkxcVRcC04+LFYdXBx1tXBVRAEP0CcHZwUXaTE/yWFFjEeHPfj3b3H3TtAaFSYanbFAFWzjFQiLmayq2LwFQEI6Mc4BmVm6nOSlITn+LqHj693UZ7lfe7P0ZvLmwzwicQxphsW8QbxzKalc94nDrOSnCM+J54w6ILEj1xXXH7jXHRY4JlhI52aJw4Ti8UOVjqYlQyVeJo4klM1yhcyLuc4b3FWKzXWuid/YSivrSxzneYIEljEEiSIUFBDGRVYiNKqkWIiRftxD/+w45fIpZCrDEaOBVShQnb84H/wu1uzMDXpJoXiQODFtj9GgeAu0Kzb9vexbTdPAP8zcKW1/dUGMPtJer2tRY6Avm3g4rqtKXvA5Q4w9KTLhuxIfppCoQC8n9E3ZYGBW6Bnze2ttY/TByBNXSVvgINDYKxI2ese7+7u7O3fM63+fgB5bXKpzZcBIwAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+gFAhArKAvJglcAAAAZdEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIEdJTVBXgQ4XAAAADElEQVQI12P4//8/AAX+Av7czFnnAAAAAElFTkSuQmCC;type=image/png'
```

The API Developer portal can be accessed at:

    http://<NGINX_INSTANCE_IP_ADDRESS>/petstore/petstore-devportal.html

### Ergast ###

Valid request:

    curl -s http://apigw.nginx.lab/ergast/2023.json | jq

Invalid request:

    curl -s http://apigw.nginx.lab/ergast/2023.json -X POST


---

**Note**: The `GitOps autosync` folder requires either
- an NGINX instance (OSS or Plus) reachable as `acme.gitlab.local` on port `80/TCP` using the sample configuration available here: [/contrib/sample-source-of-truth/ncg-nginx.conf](/contrib/sample-source-of-truth/ncg-nginx.conf)
- access to the GitHub repository at https://github.com/f5devcentral/NGINX-Declarative-API/ to fetch files under https://github.com/f5devcentral/NGINX-Declarative-API/tree/main/contrib/gitops-examples/v4.0
