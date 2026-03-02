# NGINX Declarative API — Helm Chart

This Helm chart deploys the [NGINX Declarative API](https://github.com/f5devcentral/NGINX-Declarative-API) on Kubernetes, along with its optional Web UI and Redis dependency.

NGINX Declarative API is a declarative REST API and GitOps automation layer for F5 NGINX Plus, NGINX Instance Manager, and NGINX One Console.

## Prerequisites

- Kubernetes 1.23+
- Helm 3.10+
- A running [F5 NGINX Instance Manager](https://docs.nginx.com/nginx-instance-manager/) or [F5 NGINX One Console](https://docs.nginx.com/nginx-one/) reachable from the cluster

## Installing the chart

```bash
# From the repository root
helm install nginx-declarative-api ./contrib/helm/nginx-declarative-api
```

To supply your own values file:

```bash
helm install nginx-declarative-api ./contrib/helm/nginx-declarative-api \
  -f my-values.yaml
```

## Upgrading

```bash
helm upgrade nginx-declarative-api ./contrib/helm/nginx-declarative-api \
  -f my-values.yaml
```

## Uninstalling

```bash
helm uninstall nginx-declarative-api
```

---

## Configuration

The following table lists the configurable parameters and their defaults.

### Core API

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of API pod replicas | `1` |
| `image.repository` | API container image repository | `ghcr.io/f5devcentral/nginx-declarative-api` |
| `image.tag` | API image tag (defaults to `.Chart.AppVersion`) | `""` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `service.type` | Kubernetes Service type for the API | `ClusterIP` |
| `service.port` | Service port for the API | `5000` |
| `ingress.enabled` | Enable Ingress for the API | `false` |
| `ingress.className` | Ingress class name | `""` |
| `ingress.hosts` | Ingress host rules | `[]` |
| `ingress.tls` | Ingress TLS configuration | `[]` |
| `resources` | CPU/memory resource requests and limits | `{}` |
| `nodeSelector` | Node selector labels | `{}` |
| `tolerations` | Pod tolerations | `[]` |
| `affinity` | Pod affinity rules | `{}` |

### Web UI

The Web UI provides a browser-based interface for interacting with the NGINX Declarative API. It is **disabled by default** and deployed as a separate Kubernetes Deployment and Service alongside the API.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `webui.enabled` | Enable the Web UI deployment | `false` |
| `webui.replicaCount` | Number of Web UI pod replicas | `1` |
| `webui.image.repository` | Web UI container image repository | `ghcr.io/f5devcentral/nginx-declarative-api-webui` |
| `webui.image.tag` | Web UI image tag (defaults to `.Chart.AppVersion`) | `""` |
| `webui.image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `webui.env` | Environment variables for the Web UI container | `[]` |
| `webui.service.type` | Kubernetes Service type for the Web UI | `ClusterIP` |
| `webui.service.port` | Service port for the Web UI | `80` |
| `webui.service.targetPort` | Container port the Web UI listens on | `80` |
| `webui.ingress.enabled` | Enable Ingress for the Web UI | `false` |
| `webui.ingress.className` | Ingress class name | `""` |
| `webui.ingress.annotations` | Ingress annotations | `{}` |
| `webui.ingress.hosts` | Ingress host rules | `[{host: nginx-declarative-api-ui.local, paths: [{path: /, pathType: Prefix}]}]` |
| `webui.ingress.tls` | Ingress TLS configuration | `[]` |
| `webui.resources` | CPU/memory resource requests and limits | `{}` |
| `webui.nodeSelector` | Node selector labels | `{}` |
| `webui.tolerations` | Pod tolerations | `[]` |
| `webui.affinity` | Pod affinity rules | `{}` |
| `webui.podAnnotations` | Annotations added to Web UI pods | `{}` |
| `webui.extraLabels` | Extra labels added to all Web UI resources | `{}` |
| `webui.serviceAccount.create` | Create a dedicated ServiceAccount for the Web UI | `false` |
| `webui.serviceAccount.name` | ServiceAccount name (auto-generated if empty) | `""` |
| `webui.serviceAccount.annotations` | ServiceAccount annotations | `{}` |

---

## Deploying the Web UI

### Minimal enablement (in-cluster only)

The simplest way to enable the Web UI is to set `webui.enabled=true`. The Web UI will be reachable inside the cluster via its ClusterIP Service.

```yaml
# webui-values.yaml
webui:
  enabled: true
  env:
    - name: NGINX_DECLARATIVE_API_URL
      # In-cluster URL of the NGINX Declarative API service.
      # The Web UI uses this URL to proxy API requests from the browser.
      value: "http://nginx-declarative-api:5000"
```

```bash
helm upgrade --install nginx-declarative-api ./contrib/helm/nginx-declarative-api \
  -f webui-values.yaml
```

### Exposing the Web UI via Ingress

For external access, enable the Ingress resource and provide a hostname. The example below uses the NGINX Ingress Controller with cert-manager for TLS.

```yaml
# webui-ingress-values.yaml
webui:
  enabled: true
  env:
    - name: NGINX_DECLARATIVE_API_URL
      # Must be a URL reachable from the END USER'S BROWSER — not just in-cluster.
      # Typically this is the Ingress hostname (or LoadBalancer IP) of the API itself.
      value: "https://nginx-declarative-api.example.com"

  ingress:
    enabled: true
    className: nginx
    annotations:
      cert-manager.io/cluster-issuer: letsencrypt-prod
    hosts:
      - host: nginx-declarative-api-ui.example.com
        paths:
          - path: /
            pathType: Prefix
    tls:
      - secretName: nginx-declarative-api-ui-tls
        hosts:
          - nginx-declarative-api-ui.example.com
```

```bash
helm upgrade --install nginx-declarative-api ./contrib/helm/nginx-declarative-api \
  -f webui-ingress-values.yaml
```

The Web UI will then be available at `https://nginx-declarative-api-ui.example.com`.

### Exposing the Web UI via NodePort or LoadBalancer

If you prefer not to use an Ingress controller:

```yaml
webui:
  enabled: true
  service:
    type: LoadBalancer   # or NodePort
    port: 80
  env:
    - name: NGINX_DECLARATIVE_API_URL
      value: "http://<API-EXTERNAL-IP>:5000"
```

### Port-forwarding for local testing

After a minimal install, use `kubectl port-forward` to reach the Web UI locally:

```bash
# Forward the Web UI
kubectl port-forward svc/nginx-declarative-api-webui 8080:80 &

# Forward the API (so the browser can reach it at localhost:5000)
kubectl port-forward svc/nginx-declarative-api 5000:5000 &
```

Then open `http://localhost:8080` in your browser, with the API URL configured as `http://localhost:5000`.

---

## Accessing the API Documentation

When the API is running, its built-in REST documentation is available at:

| Path | Description |
|------|-------------|
| `/docs` | Interactive Swagger UI (documentation + testing) |
| `/redoc` | Redoc documentation |
| `/openapi.json` | Raw OpenAPI specification |

---

## Architecture

When both the API and Web UI are enabled, the chart deploys:

```
┌─────────────────────────────────────────────────────┐
│  Kubernetes Namespace                               │
│                                                     │
│  ┌─────────────────┐      ┌──────────────────────┐  │
│  │  Web UI Pod     │      │  API Pod             │  │
│  │  (webui)        │      │  (nginx-decl-api)    │  │
│  │  port: 80       │      │  port: 5000          │  │
│  └────────┬────────┘      └──────────┬───────────┘  │
│           │                          │              │
│  ┌────────▼────────┐      ┌──────────▼───────────┐  │
│  │  Service        │      │  Service             │  │
│  │  *-webui :80    │      │  *-api    :5000      │  │
│  └────────┬────────┘      └──────────┬───────────┘  │
│           │                          │              │
│  ┌────────▼──────────────────────────▼───────────┐  │
│  │  Ingress (optional, one per component)        │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

The Web UI communicates with the NGINX Declarative API **from the user's browser**, not from inside the cluster. This means `webui.env[NGINX_DECLARATIVE_API_URL]` must be a URL that the browser can reach directly — typically the external hostname or IP of the API's Ingress or LoadBalancer Service.

---

## Example: Full production-style values

```yaml
# production-values.yaml

replicaCount: 2

image:
  repository: ghcr.io/f5devcentral/nginx-declarative-api
  tag: "5.5.0"

service:
  type: ClusterIP
  port: 5000

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: nginx-declarative-api.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: nginx-declarative-api-tls
      hosts:
        - nginx-declarative-api.example.com

resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi

# ── Web UI ────────────────────────────────────────────
webui:
  enabled: true

  image:
    repository: ghcr.io/f5devcentral/nginx-declarative-api-webui
    tag: "5.5.0"

  env:
    - name: NGINX_DECLARATIVE_API_URL
      value: "https://nginx-declarative-api.example.com"

  ingress:
    enabled: true
    className: nginx
    annotations:
      cert-manager.io/cluster-issuer: letsencrypt-prod
    hosts:
      - host: nginx-declarative-api-ui.example.com
        paths:
          - path: /
            pathType: Prefix
    tls:
      - secretName: nginx-declarative-api-ui-tls
        hosts:
          - nginx-declarative-api-ui.example.com

  resources:
    requests:
      cpu: 100m
      memory: 64Mi
    limits:
      cpu: 200m
      memory: 128Mi
```

---

## Related resources

- [NGINX Declarative API source](https://github.com/f5devcentral/NGINX-Declarative-API)
- [Web UI source](https://github.com/f5devcentral/NGINX-Declarative-API/tree/main/webui)
- [API usage guide (v5.5)](https://github.com/f5devcentral/NGINX-Declarative-API/blob/main/USAGE-v5.5.md)
- [Docker Compose deployment](https://github.com/f5devcentral/NGINX-Declarative-API/tree/main/contrib/docker-compose)
- [Postman collection](https://github.com/f5devcentral/NGINX-Declarative-API/tree/main/contrib/postman)
- [F5 NGINX Instance Manager docs](https://docs.nginx.com/nginx-instance-manager/)
- [F5 NGINX One Console docs](https://docs.nginx.com/nginx-one/)
