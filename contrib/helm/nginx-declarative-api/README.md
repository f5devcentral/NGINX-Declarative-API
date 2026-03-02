# NGINX Declarative API — Helm Chart

This Helm chart deploys the [NGINX Declarative API](https://github.com/f5devcentral/NGINX-Declarative-API) on Kubernetes, together with its optional **Developer Portal** service, **Web UI**, and **Redis** dependency.

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
  --set nginxDapi.image.repository=nginx-declarative-api \
  --set nginxDapi.image.tag=5.5.2
```

With all components (API + Developer Portal + Web UI):
```bash
helm install nginx-dapi . \
  --namespace nginx-dapi \
  --create-namespace \
  --set nginxDapi.enabled=true \
  --set nginxDapi.image.repository=nginx-declarative-api \
  --set nginxDapi.image.tag=5.5.2 \
  --set devportal.enabled=true \
  --set devportal.image.repository=nginx-declarative-api-devportal \
  --set devportal.image.tag=5.5.2 \
  --set webui.enabled=true \
  --set webui.image.repository=nginx-declarative-api-webui \
  --set webui.image.tag=5.5.2 \
  --set ingress.host=nginx-dapi.example.com \
  --set ingress.webuiHost=nginx-dapi-ui.example.com
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

The chart can deploy up to four components. All communicate in-cluster over ClusterIP Services:
```
                          ┌──────────────────────────────────────────────┐
                          │  Kubernetes Namespace                        │
                          │                                              │
 Browser / CI/CD ────────▶│  ┌─────────────┐     ┌───────────────────┐   │
                          │  │  Web UI     │     │  NGINX Decl. API  │   │
                          │  │  :80        │────▶│  :5000            │   │
                          │  └─────────────┘     └─────────┬─────────┘   │
                          │                                │             │
                          │                      ┌─────────▼──────────┐  │
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
| **Redis** | Queue and state store for the API | No — in-cluster only |

---

## Configuration

### Core API (`nginxDapi`)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `nginxDapi.enabled` | Enable the NGINX Declarative API deployment | `true` |
| `nginxDapi.replicaCount` | Number of API pod replicas | `1` |
| `nginxDapi.image.repository` | Container image repository | `nginx-declarative-api` |
| `nginxDapi.image.tag` | Image tag (defaults to `.Chart.AppVersion`) | `""` |
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
| `devportal.enabled` | Enable the Developer Portal service deployment | `false` |
| `devportal.replicaCount` | Number of Developer Portal pod replicas | `1` |
| `devportal.image.repository` | Container image repository | `nginx-declarative-api-devportal` |
| `devportal.image.tag` | Image tag (defaults to `.Chart.AppVersion`) | `""` |
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
| `webui.enabled` | Enable the Web UI deployment | `false` |
| `webui.replicaCount` | Number of Web UI pod replicas | `1` |
| `webui.image.repository` | Container image repository | `nginx-declarative-api-webui` |
| `webui.image.tag` | Image tag (defaults to `.Chart.AppVersion`) | `""` |
| `webui.image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `webui.env` | Environment variables injected into the Web UI container | `[]` |
| `webui.service.type` | Kubernetes Service type | `ClusterIP` |
| `webui.service.port` | Service port | `80` |
| `webui.service.targetPort` | Container port the Web UI listens on | `80` |
| `webui.ingress.enabled` | Enable Ingress for the Web UI | `false` |
| `webui.ingress.className` | Ingress class name | `""` |
| `webui.ingress.annotations` | Ingress annotations | `{}` |
| `webui.ingress.hosts` | Ingress host rules | `[]` |
| `webui.ingress.tls` | Ingress TLS configuration | `[]` |
| `webui.resources` | CPU/memory resource requests and limits | `{}` |
| `webui.nodeSelector` | Node selector labels | `{}` |
| `webui.tolerations` | Pod tolerations | `[]` |
| `webui.affinity` | Pod affinity rules | `{}` |
| `webui.podAnnotations` | Annotations added to Web UI pods | `{}` |
| `webui.extraLabels` | Extra labels added to all Web UI resources | `{}` |

---

## Deploying the Developer Portal

### Enabling the service
```bash
helm install nginx-dapi . \
  --namespace nginx-dapi --create-namespace \
  --set nginxDapi.enabled=true \
  --set nginxDapi.image.repository=nginx-declarative-api \
  --set nginxDapi.image.tag=5.5.2 \
  --set devportal.enabled=true \
  --set devportal.image.repository=nginx-declarative-api-devportal \
  --set devportal.image.tag=5.5.2
```

### In-cluster service name

When `devportal.enabled=true`, the chart creates a Service named:
```
<release-name>-nginx-declarative-api-devportal
```

For example, with release name `nginx-dapi`:
```
nginx-dapi-nginx-declarative-api-devportal
```

The NGINX Declarative API resolves this automatically via in-cluster DNS. No extra configuration is needed.

### Triggering developer portal generation

Set `developer_portal.enabled: true` in the `apigateway` block of your declarative JSON. Both `redocly` and `backstage` portal types are supported:
```json
{
  "declaration": {
    "http": {
      "servers": [
        {
          "locations": [
            {
              "uri": "/petstore",
              "apigateway": {
                "openapi_schema": "https://petstore3.swagger.io/api/v3/openapi.json",
                "api_gateway": {
                  "enabled": true,
                  "strip_uri": true,
                  "server_url": "https://petstore3.swagger.io/api/v3"
                },
                "developer_portal": {
                  "enabled": true,
                  "type": "redocly",
                  "uri": "/petstore-devportal.html"
                }
              }
            }
          ]
        }
      ]
    }
  }
}
```

The API calls the Developer Portal service to generate the portal definition, then publishes it to NGINX via NGINX Instance Manager or NGINX One Console as part of the normal config push.

### Verifying the Developer Portal is running
```bash
# Pod is Running
kubectl get pods -n nginx-dapi -l app.kubernetes.io/component=devportal

# Service exists
kubectl get svc -n nginx-dapi | grep devportal

# Tail logs to confirm requests from the API are received
kubectl logs -n nginx-dapi -l app.kubernetes.io/component=devportal -f
```

---

## Deploying the Web UI

### Determining the correct API service name

The API service name follows this pattern:
```
<release-name>-nginx-declarative-api-nginx-dapi
```

With release name `nginx-dapi` it is:
```
nginx-dapi-nginx-declarative-api-nginx-dapi
```

Confirm after installation:
```bash
kubectl get svc -n nginx-dapi
```

### Enabling the Web UI

```bash
helm install nginx-dapi . \
  --namespace nginx-dapi --create-namespace \
  --set nginxDapi.enabled=true \
  --set nginxDapi.image.repository=nginx-declarative-api \
  --set nginxDapi.image.tag=5.5.2 \
  --set webui.enabled=true \
  --set webui.image.repository=nginx-declarative-api-webui \
  --set webui.image.tag=5.5.2
```

Or via values file (recommended):
```yaml
webui:
  enabled: true
  image:
    repository: nginx-declarative-api-webui
    tag: "5.5.2"
```

### Exposing the Web UI via Ingress
```yaml
webui:
  enabled: true
  image:
    repository: nginx-declarative-api-webui
    tag: "5.5.2"
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

### Port-forwarding for local testing
```bash
kubectl port-forward -n nginx-dapi \
  svc/nginx-dapi-nginx-declarative-api-webui 8080:80
```

Open `http://localhost:8080` in your browser.

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
    repository: nginx-declarative-api
    tag: "5.5.2"
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
    repository: nginx-declarative-api-devportal
    tag: "5.5.2"
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
    repository: nginx-declarative-api-webui
    tag: "5.5.2"
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
```bash
helm install nginx-dapi . \
  --namespace nginx-dapi --create-namespace \
  -f production-values.yaml
```

---

## Troubleshooting

### Developer Portal not generating portals

1. Confirm the pod is Running: `kubectl get pods -n nginx-dapi -l app.kubernetes.io/component=devportal`
2. Confirm the service exists: `kubectl get svc -n nginx-dapi | grep devportal`
3. Confirm `developer_portal.enabled: true` is set in the declarative JSON payload
4. Check API logs for connection errors to the devportal: `kubectl logs -n nginx-dapi -l app.kubernetes.io/component=nginx-dapi`

### Checking all deployed services
```bash
kubectl get pods,svc -n nginx-dapi
```

Expected with all components enabled (release name `nginx-dapi`):
```
NAME                                                                    READY   STATUS
pod/nginx-dapi-nginx-declarative-api-devportal-<hash>                  1/1     Running
pod/nginx-dapi-nginx-declarative-api-nginx-dapi-<hash>                 1/1     Running
pod/nginx-dapi-nginx-declarative-api-redis-<hash>                      1/1     Running
pod/nginx-dapi-nginx-declarative-api-webui-<hash>                      1/1     Running

NAME                                                     TYPE        PORT(S)
service/nginx-dapi-nginx-declarative-api-devportal       ClusterIP   5000/TCP
service/nginx-dapi-nginx-declarative-api-nginx-dapi      ClusterIP   5000/TCP
service/nginx-dapi-nginx-declarative-api-redis           ClusterIP   6379/TCP
service/nginx-dapi-nginx-declarative-api-webui           ClusterIP   80/TCP
```

---

## Related resources

- [NGINX Declarative API source](https://github.com/f5devcentral/NGINX-Declarative-API)
- [Developer Portal source](https://github.com/f5devcentral/NGINX-Declarative-API/tree/main/contrib/redocly/devportal)
- [Web UI source](https://github.com/f5devcentral/NGINX-Declarative-API/tree/main/webui)
- [API usage guide v5.5](https://github.com/f5devcentral/NGINX-Declarative-API/blob/main/USAGE-v5.5.md)
- [Docker Compose deployment](https://github.com/f5devcentral/NGINX-Declarative-API/tree/main/contrib/docker-compose)
- [Postman collection](https://github.com/f5devcentral/NGINX-Declarative-API/tree/main/contrib/postman)
- [F5 NGINX Instance Manager docs](https://docs.nginx.com/nginx-instance-manager/)
- [F5 NGINX One Console docs](https://docs.nginx.com/nginx-one/)
