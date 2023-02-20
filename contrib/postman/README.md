# Sample Postman Collection

This collection contains:

API v2
- `Configuration generation` - Declaration examples with output to plaintext, JSON, Kubernetes ConfigMap, HTTP POST
- `Declarative automation - NGINX App Protect WAF` - Sample requests for declarative configuration lifecycle management
- `Declarative automation - GitOps` - GitOps automation demo
- `CRUD automation` - Sample requests for CRUD-based automation
- `Erase configuration` - Erase NGINX Plus configuration

---

API v1 - deprecated
- `Standard` - Declaration examples with output to plaintext, JSON, Kubernetes ConfigMap, HTTP POST, publish through NGINX Instance Manager
- `GitOps` - Declaration for autosync NGINX services based on CI/CD source of truth

**Note**: The `GitOps` folder requires either
- an NGINX instance (OSS or Plus) reachable as `acme.gitlab.local` on port `80/TCP` using the sample configuration available here: [/contrib/sample-source-of-truth/ncg-nginx.conf](/contrib/sample-source-of-truth/ncg-nginx.conf)
- access to the GitHub repository at https://github.com/fabriziofiorucci/NGINX-Declarative-API/ to fetch files under https://github.com/fabriziofiorucci/NGINX-Declarative-API/tree/main/contrib/sample-source-of-truth/configs
