# NGINX Declarative API — Helm Chart

This Helm chart deploys the [NGINX Declarative API](https://github.com/f5devcentral/NGINX-Declarative-API) on Kubernetes, together with its optional **Developer Portal** service, **Web UI**, **MCP Server** (Model Context Protocol), and **Redis** dependency.

NGINX Declarative API is a declarative REST API and GitOps automation layer for F5 NGINX Plus, NGINX Instance Manager, and NGINX One Console.

## Prerequisites

- Kubernetes 1.23+
- Helm 3.10+
- A running [F5 NGINX Instance Manager](https://docs.nginx.com/nginx-instance-manager/) or [F5 NGINX One Console](https://docs.nginx.com/nginx-one/) reachable from the cluster

## Installing the chart

With the core API only:
```bash
helm install nginx-dapi . \
  --namespace nginx-dapi \
  --create-namespace \
  --set nginxDapi.enabled=true \
  --set nginxDapi.image.repository=ghcr.io/f5devcentral/nginx-declarative-api \
  --set nginxDapi.image.tag=latest
```

With all components (API + Developer Portal + Web UI + MCP Server):
```bash
helm install nginx-dapi . \
  --namespace nginx-dapi \
  --create-namespace \
  --set nginxDapi.enabled=true \
  --set nginxDapi.image.repository=ghcr.io/f5devcentral/nginx-declarative-api \
  --set nginxDapi.image.tag=latest \
  --set devportal.enabled=true \
  --set devportal.image.repository=ghcr.io/f5devcentral/nginx-declarative-api-devportal \
  --set devportal.image.tag=latest \
  --set webui.enabled=true \
  --set webui.image.repository=ghcr.io/f5devcentral/nginx-declarative-api-webui \
  --set webui.image.tag=latest \
  --set mcp.enabled=true \
  --set mcp.image.repository=ghcr.io/f5devcentral/nginx-declarative-api-mcp \
  --set mcp.image.tag=latest \
  --set ingress.host=nginx-dapi.example.com \
  --set ingress.webuiHost=nginx-dapi-ui.example.com \
  --set ingress.mcpHost=nginx-dapi-mcp.example.com
```

## Upgrading
```bash
helm upgrade <release-name> . --namespace <namespace> -f my-values.yaml
```

## Uninstalling
```bash
helm uninstall <release-name> --namespace <namespace>
```

---

## Architecture overview

The chart can deploy up to five components. All communicate in-cluster over ClusterIP Services:
```
                          ┌──────────────────────────────────────────────┐
                          │  Kubernetes Namespace                        │
                          │                                              │
 Browser / CI/CD ────────▶│  ┌─────────────┐     ┌───────────────────┐   │
                          │  │  Web UI     │     │  NGINX Decl. API  │   │
                          │  │  :80        │────▶│  :5000            │   │
                          │  └─────────────┘     └─────────┬─────────┘   │
                          │                                │             │
 AI / LLMs ──────────────▶│  ┌─────────────┐               │             │
                          │  │  MCP Server │───────────────┤             │
                          │  │  :8001      │               │             │
                          │  └─────────────┘     ┌─────────▼──────────┐  │
                          │                      │  Developer Portal  │  │
                          │                      │  :5000             │  │
                          │                      └────────────────────┘  │
                          │                                              │
                          │                      ┌────────────────────┐  │
                          │                      │  Redis             │  │
                          │                      │  :6379             │  │
                          │                      └────────────────────┘  │
                          └──────────────────────────────────────────────┘
```

| Component | Purpose | External access needed? |
|-----------|---------|------------------------|
| **NGINX Declarative API** (`nginxDapi`) | Core REST API — processes declarative JSON and publishes NGINX configs to NGINX Instance Manager / NGINX One Console | Yes |
| **Developer Portal** (`devportal`) | Internal service called by the API to generate Redocly and Backstage developer portal definitions | No — in-cluster only |
| **Web UI** (`webui`) | Browser-based interface for interacting with the API | Yes |
| **MCP Server** (`mcp`) | Model Context Protocol server enabling LLMs (Claude, AGY, Cursor, ChatGPT) to interact with the API via SSE or stdio | Yes (for SSE mode) |
| **Redis** | Queue and state store for the API | No — in-cluster only |

---

## Configuration

### Core API (`nginxDapi`)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `nginxDapi.enabled` | Enable the NGINX Declarative API deployment | `true` |
| `nginxDapi.replicaCount` | Number of API pod replicas | `1` |
| `nginxDapi.image.repository` | Container image repository | `ghcr.io/f5devcentral/nginx-declarative-api` |
| `nginxDapi.image.tag` | Image tag (defaults to `.Chart.AppVersion`) | `latest` |
| `nginxDapi.image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `nginxDapi.service.type` | Kubernetes Service type | `ClusterIP` |
| `nginxDapi.service.port` | Service port | `5000` |
| `nginxDapi.ingress.enabled` | Enable Ingress for the API | `false` |
| `nginxDapi.ingress.className` | Ingress class name | `""` |
| `nginxDapi.ingress.annotations` | Ingress annotations | `{}` |
| `nginxDapi.ingress.hosts` | Ingress host rules | `[]` |
| `nginxDapi.ingress.tls` | Ingress TLS configuration | `[]` |
| `nginxDapi.resources` | CPU/memory resource requests and limits | `{}` |
| `nginxDapi.nodeSelector` | Node selector labels | `{}` |
| `nginxDapi.tolerations` | Pod tolerations | `[]` |
| `nginxDapi.affinity` | Pod affinity rules | `{}` |

### Developer Portal (`devportal`)

The Developer Portal service generates API developer portal definitions (Redocly and Backstage are supported) on behalf of the NGINX Declarative API. It is the Kubernetes equivalent of the `devportal` container in the docker-compose setup (where it runs on internal port 5000, mapped to 5001 externally).

The API calls it automatically whenever a declarative configuration includes `developer_portal.enabled: true` inside an `apigateway` location block. **No additional API-side configuration is required** — the chart wires service discovery between the two automatically.

> **This is a backend-only service.** It has no externally accessible interface and does not need an Ingress.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `devportal.enabled` | Enable the Developer Portal service deployment | `true` |
| `devportal.replicaCount` | Number of Developer Portal pod replicas | `1` |
| `devportal.image.repository` | Container image repository | `ghcr.io/f5devcentral/nginx-declarative-api-devportal` |
| `devportal.image.tag` | Image tag (defaults to `.Chart.AppVersion`) | `latest` |
| `devportal.image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `devportal.service.type` | Kubernetes Service type | `ClusterIP` |
| `devportal.service.port` | Service port | `5000` |
| `devportal.resources` | CPU/memory resource requests and limits | `{}` |
| `devportal.nodeSelector` | Node selector labels | `{}` |
| `devportal.tolerations` | Pod tolerations | `[]` |
| `devportal.affinity` | Pod affinity rules | `{}` |
| `devportal.podAnnotations` | Annotations added to Developer Portal pods | `{}` |
| `devportal.extraLabels` | Extra labels added to all Developer Portal resources | `{}` |

### Web UI (`webui`)

The Web UI runs an nginx reverse proxy that forwards API calls from the browser to the NGINX Declarative API.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `webui.enabled` | Enable the Web UI deployment | `true` |
| `webui.replicaCount` | Number of Web UI pod replicas | `1` |
| `webui.image.repository` | Container image repository | `ghcr.io/f5devcentral/nginx-declarative-api-webui` |
| `webui.image.tag` | Image tag (defaults to `.Chart.AppVersion`) | `latest` |
| `webui.image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `webui.env` | Environment variables injected into the Web UI container | `[]` |
| `webui.service.type` | Kubernetes Service type | `ClusterIP` |
| `webui.service.port` | Service port | `80` |
| `webui.service.targetPort` | Container port the Web UI listens on | `80` |
| `webui.resources` | CPU/memory resource requests and limits | `{}` |
| `webui.nodeSelector` | Node selector labels | `{}` |
| `webui.tolerations` | Pod tolerations | `[]` |
| `webui.affinity` | Pod affinity rules | `{}` |
| `webui.podAnnotations` | Annotations added to Web UI pods | `{}` |
| `webui.extraLabels` | Extra labels added to all Web UI resources | `{}` |

### MCP Server (`mcp`)

The MCP Server module provides a Model Context Protocol interface allowing AI assistants and LLM tools to construct, validate, submit, update, and manage NGINX Declarative API configurations using natural language.

In Kubernetes, the MCP Server runs in streamable-http mode on port 8001 by default and connects to the NGINX Declarative API via `NDAPI_BASE_URL`.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `mcp.enabled` | Enable the MCP Server deployment | `true` |
| `mcp.replicaCount` | Number of MCP Server pod replicas | `1` |
| `mcp.image.repository` | Container image repository | `ghcr.io/f5devcentral/nginx-declarative-api-mcp` |
| `mcp.image.tag` | Image tag | `latest` |
| `mcp.image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `mcp.containerPort` | Container port for HTTP transport | `8001` |
| `mcp.args` | Optional CLI arguments passed to container entrypoint | `[]` |
| `mcp.service.type` | Kubernetes Service type | `ClusterIP` |
| `mcp.service.port` | Service port | `8001` |
| `mcp.env` | Additional environment variables for MCP Server | `[]` |
| `mcp.resources` | CPU/memory resource requests and limits | `{}` |
| `mcp.nodeSelector` | Node selector labels | `{}` |
| `mcp.tolerations` | Pod tolerations | `[]` |
| `mcp.affinity` | Pod affinity rules | `{}` |
| `mcp.podAnnotations` | Annotations added to MCP pods | `{}` |

---

## Deploying the MCP Server

### Enabling the MCP service

```bash
helm install nginx-dapi . \
  --namespace nginx-dapi --create-namespace \
  --set nginxDapi.enabled=true \
  --set mcp.enabled=true \
  --set mcp.image.repository=ghcr.io/f5devcentral/nginx-declarative-api-mcp \
  --set mcp.image.tag=latest
```

Or via values file:
```yaml
mcp:
  enabled: true
  image:
    repository: ghcr.io/f5devcentral/nginx-declarative-api-mcp
    tag: "latest"
```

### In-cluster service discovery

The MCP Server connects to the NGINX Declarative API in-cluster using `NDAPI_BASE_URL`:
```
http://nginx-dapi:5000
```
This is automatically injected into the MCP container by the deployment template.

### Connecting AI Clients via SSE

Port-forward the MCP service to expose the SSE endpoint locally:
```bash
kubectl port-forward -n nginx-dapi \
  svc/nginx-dapi-nginx-declarative-api-mcp 8001:8001
```

Configure your MCP-compliant client (e.g. Claude Desktop, Cursor, or Antigravity) to connect to `http://localhost:8001/sse`.

### Exposing MCP via Ingress

Set `ingress.mcpHost` in your values:
```yaml
ingress:
  enabled: true
  className: nginx
  mcpHost: nginx-dapi-mcp.example.com
```

---

## Deploying the Developer Portal

### Enabling the service
```bash
helm install nginx-dapi . \
  --namespace nginx-dapi --create-namespace \
  --set nginxDapi.enabled=true \
  --set devportal.enabled=true \
  --set devportal.image.repository=ghcr.io/f5devcentral/nginx-declarative-api-devportal \
  --set devportal.image.tag=latest
```

### In-cluster service name

When `devportal.enabled=true`, the chart creates a Service named `devportal` (or `<release-name>-nginx-declarative-api-devportal`). The NGINX Declarative API resolves this automatically via in-cluster DNS.

---

## Deploying the Web UI

### Enabling the Web UI

```bash
helm install nginx-dapi . \
  --namespace nginx-dapi --create-namespace \
  --set nginxDapi.enabled=true \
  --set webui.enabled=true \
  --set webui.image.repository=ghcr.io/f5devcentral/nginx-declarative-api-webui \
  --set webui.image.tag=latest
```

---

## Accessing the API documentation

| Path | Description |
|------|-------------|
| `/docs` | Interactive Swagger UI |
| `/redoc` | Redoc documentation |
| `/openapi.json` | Raw OpenAPI specification |

Port-forward to access locally:
```bash
kubectl port-forward -n nginx-dapi \
  svc/nginx-dapi-nginx-declarative-api-nginx-dapi 5000:5000
```

Then open `http://localhost:5000/docs`.

---

## Full production example
```yaml
# production-values.yaml

nginxDapi:
  enabled: true
  image:
    repository: ghcr.io/f5devcentral/nginx-declarative-api
    tag: "latest"
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

devportal:
  enabled: true
  image:
    repository: ghcr.io/f5devcentral/nginx-declarative-api-devportal
    tag: "latest"
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 200m
      memory: 256Mi

webui:
  enabled: true
  image:
    repository: ghcr.io/f5devcentral/nginx-declarative-api-webui
    tag: "latest"
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

mcp:
  enabled: true
  image:
    repository: ghcr.io/f5devcentral/nginx-declarative-api-mcp
    tag: "latest"
  resources:
    requests:
      cpu: 50m
      memory: 64Mi
    limits:
      cpu: 200m
      memory: 256Mi

ingress:
  enabled: true
  className: nginx
  host: nginx-declarative-api.example.com
  webuiHost: nginx-declarative-api-ui.example.com
  mcpHost: nginx-declarative-api-mcp.example.com
```
```bash
helm install nginx-dapi . \
  --namespace nginx-dapi --create-namespace \
  -f production-values.yaml
```

---

## Troubleshooting

### Checking all deployed services
```bash
kubectl get pods,svc -n nginx-dapi
```

Expected with all components enabled (release name `nginx-dapi`):
```
NAME                                                                    READY   STATUS
pod/nginx-dapi-nginx-declarative-api-devportal-<hash>                  1/1     Running
pod/nginx-dapi-nginx-declarative-api-mcp-<hash>                        1/1     Running
pod/nginx-dapi-nginx-declarative-api-nginx-dapi-<hash>                 1/1     Running
pod/nginx-dapi-nginx-declarative-api-redis-<hash>                      1/1     Running
pod/nginx-dapi-nginx-declarative-api-webui-<hash>                      1/1     Running

NAME                                                     TYPE        PORT(S)
service/nginx-dapi-nginx-declarative-api-devportal       ClusterIP   5000/TCP
service/nginx-dapi-nginx-declarative-api-mcp             ClusterIP   8001/TCP
service/nginx-dapi-nginx-declarative-api-nginx-dapi      ClusterIP   5000/TCP
service/nginx-dapi-nginx-declarative-api-redis           ClusterIP   6379/TCP
service/nginx-dapi-nginx-declarative-api-webui           ClusterIP   80/TCP
```

---

## Related resources

- [NGINX Declarative API source](https://github.com/f5devcentral/NGINX-Declarative-API/tree/v5.7)
- [MCP Server source](https://github.com/f5devcentral/NGINX-Declarative-API/tree/v5.7/contrib/mcp)
- [Developer Portal source](https://github.com/f5devcentral/NGINX-Declarative-API/tree/v5.7/contrib/devportal)
- [Web UI source](https://github.com/f5devcentral/NGINX-Declarative-API/tree/v5.7/webui)
- [API usage guide v5.7](https://github.com/f5devcentral/NGINX-Declarative-API/blob/v5.7/USAGE-v5.7.md)
- [Docker Compose deployment](https://github.com/f5devcentral/NGINX-Declarative-API/tree/v5.7/contrib/docker-compose)
- [Postman collection](https://github.com/f5devcentral/NGINX-Declarative-API/tree/v5.7/contrib/postman)
- [F5 NGINX Instance Manager docs](https://docs.nginx.com/nginx-instance-manager/)
- [F5 NGINX One Console docs](https://docs.nginx.com/nginx-one/)
