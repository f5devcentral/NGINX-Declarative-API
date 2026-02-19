# nginx-declarative-api Helm Chart

A production-grade Helm chart for the [F5 NGINX Declarative API](https://github.com/f5devcentral/NGINX-Declarative-API) — a declarative REST API and GitOps automation layer for NGINX Plus, NGINX Instance Manager, and NGINX One Console.

![Chart Version](https://img.shields.io/badge/chart-v1.0.0-blue)
![App Version](https://img.shields.io/badge/app-v5.5.1-green)
![Kubernetes](https://img.shields.io/badge/kubernetes-%3E%3D1.24-informational)
![License](https://img.shields.io/badge/license-Apache%202.0-blue)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Chart Structure](#chart-structure)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
  - [Global](#global)
  - [NGINX Declarative API (nginxDapi)](#nginx-declarative-api-nginxdapi)
  - [Redis (redis)](#redis-redis)
  - [Developer Portal (devportal)](#developer-portal-devportal)
  - [Ingress](#ingress)
  - [Network Policy](#network-policy)
- [Environment Profiles](#environment-profiles)
- [Advanced Usage](#advanced-usage)
  - [TLS / HTTPS](#tls--https-with-cert-manager)
  - [Horizontal Pod Autoscaling](#horizontal-pod-autoscaling)
  - [Pod Anti-Affinity](#pod-anti-affinity)
  - [Image Pull Secrets](#image-pull-secrets)
  - [Loading config from a Secret](#loading-config-from-a-secret)
  - [Redis Persistent Volume](#redis-persistent-volume)
  - [External Redis](#external-redis)
- [Upgrading](#upgrading)
- [Uninstalling](#uninstalling)
- [Accessing the API](#accessing-the-api)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

This chart deploys three components as a cohesive stack:

| Component | Description | Default Port |
|-----------|-------------|:------------:|
| **nginx-dapi** | Core declarative REST API service | `5000` |
| **redis** | In-memory data store for request queuing and GitOps state | `6379` |
| **devportal** | Developer portal service (Redocly / Backstage integration) | `5000` |

Each component can be independently enabled, disabled, scaled, and configured. All resource names are release-scoped so multiple instances can coexist in the same cluster without conflict.

---

## Architecture

```
                         ┌─────────────────────────────────┐
                         │         Kubernetes Cluster        │
                         │                                   │
  External Traffic ──▶  Ingress (nginx-dapi.example.com)    │
                         │         │                         │
                         │         ▼                         │
                         │   ┌───────────┐                   │
                         │   │ nginx-dapi│ (:5000)           │
                         │   └─────┬─────┘                   │
                         │         │                         │
                         │    ┌────┴─────┐                   │
                         │    │          │                   │
                         │    ▼          ▼                   │
                         │  ┌─────┐  ┌──────────┐           │
                         │  │Redis│  │devportal │           │
                         │  │:6379│  │  :5000   │           │
                         │  └─────┘  └──────────┘           │
                         └─────────────────────────────────┘
```

When `networkPolicy.enabled: true`, traffic between components is enforced at the Kubernetes network layer — only `nginx-dapi` can reach `redis` and `devportal`, and Redis is fully isolated from external access.

---

## Prerequisites

- Kubernetes **≥ 1.24**
- Helm **≥ 3.10**
- A container registry hosting the `nginx-declarative-api` and `nginx-declarative-api-devportal` images (see the upstream [project README](https://github.com/f5devcentral/NGINX-Declarative-API) for build instructions)
- An NGINX Ingress Controller deployed in the cluster (if `ingress.enabled: true`)
- [cert-manager](https://cert-manager.io/) *(optional, for automatic TLS provisioning)*

---

## Chart Structure

```
nginx-declarative-api/
├── Chart.yaml
├── README.md
├── values.yaml                        # Full default configuration
├── values-dev.yaml                    # Lightweight dev/local overrides
├── values-production.yaml             # Production-hardened overrides
└── templates/
    ├── _helpers.tpl                   # Named template helpers
    ├── NOTES.txt                      # Post-install instructions
    ├── serviceaccount.yaml            # ServiceAccounts for dapi + devportal
    ├── deployment-nginx-dapi.yaml     # Main API deployment
    ├── deployment-redis.yaml          # Redis deployment
    ├── deployment-devportal.yaml      # Developer portal deployment
    ├── service.yaml                   # ClusterIP services for all 3 components
    ├── ingress.yaml                   # Ingress with optional TLS + path routing
    ├── hpa.yaml                       # HorizontalPodAutoscalers
    ├── pdb.yaml                       # PodDisruptionBudgets
    ├── pvc.yaml                       # PersistentVolumeClaims
    └── networkpolicy.yaml             # NetworkPolicies for traffic isolation
```

---

## Quick Start

### 1. Set your image registries

Before deploying, set the image repositories either in `values.yaml` or via `--set`:

```yaml
nginxDapi:
  image:
    repository: "registry.example.com/nginx-declarative-api"
    tag: "5.5.0"

devportal:
  image:
    repository: "registry.example.com/nginx-declarative-api-devportal"
    tag: "5.5.0"
```

### 2. Install the chart

```bash
helm install nginx-dapi ./nginx-declarative-api \
  --namespace nginx-dapi \
  --create-namespace \
  --set nginxDapi.image.repository=registry.example.com/nginx-declarative-api \
  --set nginxDapi.image.tag=5.5.1 \
  --set devportal.image.repository=registry.example.com/nginx-declarative-api-devportal \
  --set devportal.image.tag=5.5.1 \
  --set ingress.host=nginx-dapi.example.com
```

### 3. Verify the deployment

```bash
kubectl get pods -n nginx-dapi -l app.kubernetes.io/instance=nginx-dapi
```

Expected output:

```
NAME                                           READY   STATUS    RESTARTS   AGE
nginx-dapi-nginx-dapi-7d9f4b8c6-xkp2m         1/1     Running   0          45s
nginx-dapi-redis-6b4d9f7c5-tn8qr              1/1     Running   0          45s
nginx-dapi-devportal-5c8b6d9f4-mp3wz          1/1     Running   0          45s
```

### 4. Access the API docs

```bash
kubectl port-forward -n nginx-dapi svc/nginx-dapi-nginx-dapi 5000:5000
```

Then open:

| Endpoint | URL |
|----------|-----|
| Swagger UI | http://localhost:5000/docs |
| ReDoc | http://localhost:5000/redoc |
| OpenAPI spec | http://localhost:5000/openapi.json |

---

## Configuration

### Global

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.namespaceOverride` | Override the target namespace for all resources | `""` |
| `global.imagePullSecrets` | Image pull secrets applied to every pod | `[]` |
| `global.podLabels` | Extra labels added to all pod specs | `{}` |
| `global.podAnnotations` | Extra annotations added to all pod specs | `{}` |

---

### NGINX Declarative API (`nginxDapi`)

#### Core

| Parameter | Description | Default |
|-----------|-------------|---------|
| `nginxDapi.enabled` | Deploy the nginx-dapi component | `true` |
| `nginxDapi.replicaCount` | Number of replicas (ignored when HPA is enabled) | `1` |
| `nginxDapi.containerPort` | Port the container listens on | `5000` |
| `nginxDapi.image.repository` | Container image repository | `YOUR_REGISTRY_HERE/nginx-declarative-api` |
| `nginxDapi.image.tag` | Image tag | `latest` |
| `nginxDapi.image.pullPolicy` | Image pull policy | `IfNotPresent` |

#### Service

| Parameter | Description | Default |
|-----------|-------------|---------|
| `nginxDapi.service.type` | Service type (`ClusterIP`, `NodePort`, `LoadBalancer`) | `ClusterIP` |
| `nginxDapi.service.port` | Service port | `5000` |
| `nginxDapi.service.nodePort` | NodePort number (only when `type: NodePort`) | `""` |
| `nginxDapi.service.annotations` | Annotations on the Service | `{}` |

#### Environment

| Parameter | Description | Default |
|-----------|-------------|---------|
| `nginxDapi.env` | List of extra environment variables to inject | `[]` |
| `nginxDapi.envFrom` | Load env vars from ConfigMaps or Secrets | `[]` |

> **Note:** The app reads its Redis connection details from `config.toml` baked into the Docker image (default: `redis:6379`). The bundled Redis Service is named `redis` to match this exactly. If you use an external Redis you will need to mount a custom `config.toml` — see [External Redis](#external-redis).

#### Resources, Probes & Security

| Parameter | Description | Default |
|-----------|-------------|---------|
| `nginxDapi.resources` | CPU/memory requests and limits | See `values.yaml` |
| `nginxDapi.livenessProbe` | Liveness probe (HTTP GET `/docs`) | See `values.yaml` |
| `nginxDapi.readinessProbe` | Readiness probe (HTTP GET `/docs`) | See `values.yaml` |
| `nginxDapi.podSecurityContext` | Pod-level security context | `runAsNonRoot: true`, `runAsUser: 1000` |
| `nginxDapi.containerSecurityContext` | Container security context | `allowPrivilegeEscalation: false`, caps dropped |

#### Scheduling

| Parameter | Description | Default |
|-----------|-------------|---------|
| `nginxDapi.nodeSelector` | Node selector | `{}` |
| `nginxDapi.tolerations` | Tolerations | `[]` |
| `nginxDapi.affinity` | Affinity rules | `{}` |

#### Persistence

| Parameter | Description | Default |
|-----------|-------------|---------|
| `nginxDapi.persistence.enabled` | Mount a PersistentVolumeClaim | `false` |
| `nginxDapi.persistence.storageClass` | StorageClass (`""` = cluster default) | `""` |
| `nginxDapi.persistence.accessMode` | PVC access mode | `ReadWriteOnce` |
| `nginxDapi.persistence.size` | PVC size | `1Gi` |
| `nginxDapi.persistence.existingClaim` | Use a pre-existing PVC | `""` |

#### Autoscaling

| Parameter | Description | Default |
|-----------|-------------|---------|
| `nginxDapi.autoscaling.enabled` | Enable HPA | `false` |
| `nginxDapi.autoscaling.minReplicas` | Minimum replicas | `1` |
| `nginxDapi.autoscaling.maxReplicas` | Maximum replicas | `5` |
| `nginxDapi.autoscaling.targetCPUUtilizationPercentage` | Target CPU % | `80` |
| `nginxDapi.autoscaling.targetMemoryUtilizationPercentage` | Target memory % (optional) | `""` |

#### Pod Disruption Budget

| Parameter | Description | Default |
|-----------|-------------|---------|
| `nginxDapi.podDisruptionBudget.enabled` | Create a PDB | `false` |
| `nginxDapi.podDisruptionBudget.minAvailable` | Minimum available pods | `1` |
| `nginxDapi.podDisruptionBudget.maxUnavailable` | Maximum unavailable (alternative) | `""` |

#### ServiceAccount

| Parameter | Description | Default |
|-----------|-------------|---------|
| `nginxDapi.serviceAccount.create` | Create a dedicated ServiceAccount | `true` |
| `nginxDapi.serviceAccount.name` | Override the ServiceAccount name | `""` |
| `nginxDapi.serviceAccount.annotations` | ServiceAccount annotations | `{}` |
| `nginxDapi.serviceAccount.automountServiceAccountToken` | Auto-mount API token | `false` |

---

### Redis (`redis`)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `redis.enabled` | Deploy Redis | `true` |
| `redis.image.repository` | Redis image | `redis` |
| `redis.image.tag` | Redis tag | `7.2-alpine` |
| `redis.replicaCount` | Replicas (keep at `1` for standalone) | `1` |
| `redis.containerPort` | Redis port | `6379` |
| `redis.args` | Command-line args passed to `redis-server` | persistence disabled |
| `redis.resources` | CPU/memory requests and limits | See `values.yaml` |
| `redis.persistence.enabled` | Mount a PVC for Redis data | `false` |
| `redis.persistence.size` | PVC size | `2Gi` |
| `redis.podDisruptionBudget.enabled` | Create a PDB | `false` |

> **Note:** Redis persistence is disabled by default because it is primarily used for ephemeral request queuing. Enable it if you rely on Redis for GitOps state that must survive pod restarts.

---

### Developer Portal (`devportal`)

The devportal component exposes the same parameters as `nginxDapi`. Key values:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `devportal.enabled` | Deploy the devportal | `true` |
| `devportal.image.repository` | Image repository | `YOUR_REGISTRY_HERE/nginx-declarative-api-devportal` |
| `devportal.image.tag` | Image tag | `latest` |
| `devportal.replicaCount` | Replicas | `1` |
| `devportal.autoscaling.enabled` | Enable HPA | `false` |
| `devportal.autoscaling.maxReplicas` | HPA max replicas | `3` |
| `devportal.podDisruptionBudget.enabled` | Create a PDB | `false` |

---

### Ingress

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Create an Ingress resource | `true` |
| `ingress.className` | `ingressClassName` | `nginx` |
| `ingress.annotations` | Ingress annotations | `{}` |
| `ingress.host` | Hostname for the nginx-declarative-api service | `nginx-dapi.k8s.example.com` |
| `ingress.tls` | TLS configuration | `[]` |

Set the hostname at install time — all URIs are automatically forwarded to the nginx-declarative-api service:

```bash
--set ingress.host=nginx-dapi.example.com
```

Or in `values.yaml`:

```yaml
ingress:
  host: nginx-dapi.example.com
```

---

### Network Policy

| Parameter | Description | Default |
|-----------|-------------|---------|
| `networkPolicy.enabled` | Create NetworkPolicy resources | `false` |
| `networkPolicy.extraIngress` | Extra ingress rules for nginx-dapi | `[]` |
| `networkPolicy.extraEgress` | Extra egress rules for nginx-dapi | `[]` |

When enabled: `redis` and `devportal` are only reachable from `nginx-dapi`, and all pods allow DNS egress on port 53.

---

## Environment Profiles

### Development

```bash
helm install nginx-dapi ./nginx-declarative-api \
  -f values-dev.yaml \
  -n nginx-dapi --create-namespace \
  --set nginxDapi.image.repository=registry.example.com/nginx-declarative-api \
  --set devportal.image.repository=registry.example.com/nginx-declarative-api-devportal
```

### Production

```bash
helm install nginx-dapi ./nginx-declarative-api \
  -f values-production.yaml \
  -n nginx-dapi --create-namespace \
  --set nginxDapi.image.repository=registry.example.com/nginx-declarative-api \
  --set nginxDapi.image.tag=5.5.1 \
  --set devportal.image.repository=registry.example.com/nginx-declarative-api-devportal \
  --set devportal.image.tag=5.5.1 \
  --set ingress.host=nginx-dapi.example.com
```

The production profile enables HPA, PodDisruptionBudgets, pod anti-affinity, Redis persistence, and NetworkPolicies.

---

## Advanced Usage

### TLS / HTTPS with cert-manager

```yaml
ingress:
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: nginx-dapi.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: nginx-dapi-tls
      hosts:
        - nginx-dapi.example.com
```

### Horizontal Pod Autoscaling

```yaml
nginxDapi:
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
```

> Requires [metrics-server](https://github.com/kubernetes-sigs/metrics-server) in the cluster.

### Pod Anti-Affinity

```yaml
nginxDapi:
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          podAffinityTerm:
            labelSelector:
              matchLabels:
                app.kubernetes.io/component: nginx-dapi
            topologyKey: kubernetes.io/hostname
```

### Image Pull Secrets

```bash
kubectl create secret docker-registry registry-credentials \
  --docker-server=registry.example.com \
  --docker-username=<user> \
  --docker-password=<token> \
  -n nginx-dapi
```

```yaml
global:
  imagePullSecrets:
    - name: registry-credentials
```

### Loading config from a Secret

```yaml
nginxDapi:
  envFrom:
    - secretRef:
        name: nginx-dapi-secrets
```

### Redis Persistent Volume

By default Redis runs with no persistence — data is lost if the pod restarts. This is fine for ephemeral request queuing, but if you rely on Redis for GitOps autosync state you should enable a PersistentVolumeClaim.

#### Option 1 — Let the chart create the PVC (recommended)

Set `redis.persistence.enabled: true` and the chart will automatically create a PVC named `<release>-nginx-declarative-api-redis` and mount it at `/data` inside the Redis container.

```yaml
redis:
  persistence:
    enabled: true
    size: 5Gi                # volume size
    accessMode: ReadWriteOnce
    storageClass: ""         # "" uses the cluster default StorageClass
```

Or pass the same values via `--set` at install time:

```bash
helm install nginx-dapi . \
  --namespace nginx-dapi --create-namespace \
  --set nginxDapi.image.repository=registry.example.com/nginx-declarative-api \
  --set nginxDapi.image.tag=5.5.1 \
  --set devportal.image.repository=registry.example.com/nginx-declarative-api-devportal \
  --set devportal.image.tag=5.5.1 \
  --set redis.persistence.enabled=true \
  --set redis.persistence.size=5Gi
```

Confirm the PVC was created and is bound before the pod starts:

```bash
kubectl get pvc -n nginx-dapi
# NAME                                          STATUS   VOLUME   CAPACITY   ...
# nginx-dapi-nginx-declarative-api-redis        Bound    pvc-...  5Gi        ...
```

#### Option 2 — Use a specific StorageClass

If your cluster has multiple StorageClasses (e.g. `fast-ssd`, `standard`), specify the one you want:

```yaml
redis:
  persistence:
    enabled: true
    storageClass: "fast-ssd"
    size: 5Gi
```

#### Option 3 — Use a pre-existing PVC

If you have already created a PVC manually (e.g. to migrate data), reference it by name and the chart will skip PVC creation:

```bash
# Create the PVC manually first
kubectl apply -n nginx-dapi -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-redis-data
  namespace: nginx-dapi
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 5Gi
EOF
```

```yaml
redis:
  persistence:
    enabled: true
    existingClaim: "my-redis-data"
```

#### Enabling persistence on an already-running release

If Redis is already deployed without persistence, upgrade in place:

```bash
helm upgrade nginx-dapi . \
  --namespace nginx-dapi \
  --set redis.persistence.enabled=true \
  --set redis.persistence.size=5Gi
```

> **Warning:** This will restart the Redis pod. Any in-memory data that was not previously persisted will be lost on this one restart. All subsequent restarts will retain data on the volume.

#### Verifying data survives a pod restart

```bash
# Write a test key
kubectl exec -n nginx-dapi deploy/nginx-dapi-nginx-declarative-api-redis \
  -- redis-cli set helm-test "persistence-works"

# Delete the pod (it will be recreated by the Deployment)
kubectl delete pod -n nginx-dapi -l app.kubernetes.io/component=redis

# Wait for it to come back, then read the key
kubectl exec -n nginx-dapi deploy/nginx-dapi-nginx-declarative-api-redis \
  -- redis-cli get helm-test
# Expected output: persistence-works
```

---

### External Redis

To disable the bundled Redis and point the app at an external instance, you need to supply a custom `config.toml` that overrides the default Redis hostname. Mount it as a volume:

```yaml
redis:
  enabled: false   # disable the bundled Redis Deployment and Service

nginxDapi:
  extraVolumes:
    - name: config
      configMap:
        name: nginx-dapi-config

  extraVolumeMounts:
    - name: config
      mountPath: /app/etc/config.toml
      subPath: config.toml
```

Create the ConfigMap with your Redis connection details before installing:

```bash
kubectl create configmap nginx-dapi-config \
  --from-literal=config.toml='
[redis]
host = "my-external-redis.example.com"
port = 6379
' \
  -n nginx-dapi
```

---

## Upgrading

```bash
helm upgrade nginx-dapi ./nginx-declarative-api \
  -n nginx-dapi \
  -f values-production.yaml \
  --set nginxDapi.image.tag=5.5.1
```

Every Deployment template includes a `checksum/values` annotation that automatically triggers a rolling restart when the corresponding values section changes.

Preview changes before applying:

```bash
# Requires the helm-diff plugin
helm diff upgrade nginx-dapi ./nginx-declarative-api -n nginx-dapi -f values-production.yaml
```

---

## Uninstalling

```bash
helm uninstall nginx-dapi -n nginx-dapi
```

> **Note:** PersistentVolumeClaims are **not** deleted automatically to prevent data loss. Remove them manually if needed:
>
> ```bash
> kubectl delete pvc -n nginx-dapi -l app.kubernetes.io/instance=nginx-dapi
> ```

---

## Accessing the API

| Endpoint | Path |
|----------|------|
| Swagger UI (interactive docs) | `/docs` |
| ReDoc documentation | `/redoc` |
| OpenAPI specification | `/openapi.json` |

---

## Troubleshooting

**Helm reports `deployed` but no pods exist**

Ensure you used `--create-namespace` or pre-created the namespace before installing. Do not create the namespace inside `values.yaml` — this causes a conflict with Helm's namespace management.

```bash
helm install nginx-dapi ./nginx-declarative-api -n nginx-dapi --create-namespace
```

**`ImagePullBackOff`**

Verify the image repository and tag, and confirm `global.imagePullSecrets` is set for private registries:

```bash
kubectl describe pod -n nginx-dapi <pod-name> | grep -A 10 "Events:"
```

**`nginx-dapi` can't reach Redis**

The app connects to Redis using the hostname `redis` hardcoded in its `config.toml`. Confirm the Redis Service exists with that exact name and is running:

```bash
kubectl get svc -n nginx-dapi
kubectl logs -n nginx-dapi deploy/nginx-dapi-nginx-declarative-api-nginx-dapi | grep -i redis
```

**Liveness probe failing on startup**

Increase `initialDelaySeconds` if the app takes longer than 15 seconds to start:

```yaml
nginxDapi:
  livenessProbe:
    initialDelaySeconds: 30
```

**Render templates without installing**

```bash
helm template nginx-dapi ./nginx-declarative-api -f values-dev.yaml
```

**Lint the chart**

```bash
helm lint ./nginx-declarative-api
```

---

## License

This Helm chart is licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).

The upstream NGINX Declarative API project is also Apache 2.0 licensed. See the [upstream repository](https://github.com/f5devcentral/NGINX-Declarative-API/blob/main/LICENSE.md) for details.
