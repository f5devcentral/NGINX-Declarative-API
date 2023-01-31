# Sample Postman Collection

This collection contains two folders:

API v1
- `Standard` - Declaration examples with output to plaintext, JSON, Kubernetes ConfigMap, HTTP POST, publish through NGINX Instance Manager
- `GitOps` - Declaration for autosync NGINX services based on CI/CD source of truth

**Note**: The `GitOps` folder requires either
- an NGINX instance (OSS or Plus) reachable as `acme.gitlab.local` on port `80/TCP` using the sample configuration available here: [/contrib/sample-source-of-truth/ncg-nginx.conf](/contrib/sample-source-of-truth/ncg-nginx.conf)
- access to the GitHub repository at https://github.com/fabriziofiorucci/NGINX-Declarative-API/ to fetch files under https://github.com/fabriziofiorucci/NGINX-Declarative-API/tree/main/contrib/sample-source-of-truth/configs

---

API v2 - alpha release
- `Standard` - Declaration examples with output to plaintext, JSON, Kubernetes ConfigMap, HTTP POST
- `NMS Output` - Work in progress
