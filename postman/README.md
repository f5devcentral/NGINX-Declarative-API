# Sample Postman Collection

This collection contains two folders:

* `Standard` - Declaration examples with output to plaintext, JSON, Kubernetes ConfigMap, HTTP POST, publish through NGINX Instance Manager
* `GitOps` - Declaration for autosync NGINX services based on CI/CD source of truth

**Note**: The `GitOps` folder requires an NGINX instance (OSS or Plus) reachable as `acme.giztlab.local` on port `80/TCP` using the sample configuration available here: [/contrib/sample-source-of-truth/ncg-nginx.conf](/contrib/sample-source-of-truth/ncg-nginx.conf)