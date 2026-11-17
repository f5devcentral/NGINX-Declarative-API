# Running NGINX Declarative API on Kubernetes

NGINX Declarative API v5.7 can be deployed on Kubernetes using the plain manifests in this directory (`nginx-declarative-api.yaml`).

> **Looking for configurable production options** (custom `values.yaml`, autoscaling, persistence, TLS, NetworkPolicies, or per-component toggles)? Use the [Helm chart](/contrib/helm/nginx-declarative-api) instead.

## Deployed Components

`nginx-declarative-api.yaml` creates the `nginx-dapi` namespace and deploys:

| Component | Service | Port | Image | Purpose |
| --- | --- | --- | --- | --- |
| **nginx-dapi** | `nginx-dapi` | `5000` | `ghcr.io/f5devcentral/nginx-declarative-api:latest` | Core Declarative REST API service (`v5.7`) |
| **devportal** | `devportal` | `5000` | `ghcr.io/f5devcentral/nginx-declarative-api-devportal:latest` | Redocly Developer Portal generator |
| **webui** | `webui` | `80` → `8080` | `ghcr.io/f5devcentral/nginx-declarative-api-webui:latest` | Browser-based Web UI (`nginx-unprivileged` on port `8080`) |
| **mcp** | `mcp` | `8800` | `ghcr.io/f5devcentral/nginx-declarative-api-mcp:latest` | Model Context Protocol (MCP) server (`streamable-http` on `/mcp`) |
| **redis** | `redis` | `6379` | `redis:8.10` | Declaration state, GitOps sync metadata, and async queue |

## Prerequisites

- Kubernetes 1.23+
- An Ingress controller matching `ingressClassName: nginx` (or update `spec.ingressClassName` in `nginx-declarative-api.yaml`), **or** a Kubernetes Gateway API `v1` controller (such as F5 NGINX Gateway Fabric) if enabling the commented-out `Gateway` + `HTTPRoute` option
- Connectivity from the cluster to [F5 NGINX Instance Manager](https://docs.f5.com/nginx-instance-manager/) or [F5 NGINX One Console](https://docs.f5.com/nginx-one-console/)

## How to Deploy

### Option A: Use pre-built GitHub Container Registry images (recommended)

1. Edit `nginx-declarative-api.yaml` and update the `Ingress` hostnames to match your DNS environment:

    ```yaml
      rules:
        - host: nginx-dapi.k8s.example.com
        - host: nginx-dapi-webui.k8s.example.com
        - host: nginx-dapi-mcp.k8s.example.com
    ```

    > **Tip:** To pin release `5.7.2` explicitly instead of `:latest`, replace the `:latest` tags on the four `ghcr.io/f5devcentral/nginx-declarative-api*` images (or configure `NDAPI_VERSION` / `NDAPI_API_KEY` on the `mcp` Deployment if authentication is enabled).

2. Apply the manifest:

    ```shell
    kubectl apply -f nginx-declarative-api.yaml
    ```

    Expected output:

    ```text
    namespace/nginx-dapi created
    deployment.apps/redis created
    service/redis created
    deployment.apps/nginx-dapi created
    service/nginx-dapi created
    deployment.apps/devportal created
    service/devportal created
    deployment.apps/webui created
    service/webui created
    deployment.apps/mcp created
    service/mcp created
    ingress.networking.k8s.io/nginx-dapi created
    ```

3. Verify all pods and services are running:

    ```shell
    kubectl get all -n nginx-dapi
    ```

    Expected output:

    ```text
    NAME                              READY   STATUS    RESTARTS   AGE
    pod/devportal-xxxxxxxxxx-xxxxx    1/1     Running   0          30s
    pod/mcp-xxxxxxxxxx-xxxxx          1/1     Running   0          30s
    pod/nginx-dapi-xxxxxxxxxx-xxxxx   1/1     Running   0          30s
    pod/redis-xxxxxxxxxx-xxxxx        1/1     Running   0          30s
    pod/webui-xxxxxxxxxx-xxxxx        1/1     Running   0          30s
    ```

4. Inspect the `Ingress` endpoints:

    ```shell
    kubectl get ingress -n nginx-dapi
    ```

    - **REST API & Swagger docs:** `http://nginx-dapi.k8s.example.com/docs` (plus `/redoc` and `/openapi.json`)
    - **Web UI:** `http://nginx-dapi-webui.k8s.example.com/`
    - **MCP Server (Streamable HTTP):** `http://nginx-dapi-mcp.k8s.example.com/mcp` (see [contrib/mcp/README.md](/contrib/mcp/README.md) for client setup)

### Option B: Build and push custom images to a private registry

1. Build all images locally using the [Docker Compose helper script](/contrib/docker-compose):

    ```shell
    cd contrib/docker-compose
    ./nginx-dapi.sh -c build
    ```

2. Tag and push the four built images to your registry:

    ```shell
    for img in \
      nginx-declarative-api \
      nginx-declarative-api-devportal \
      nginx-declarative-api-webui \
      nginx-declarative-api-mcp
    do
      docker tag ghcr.io/f5devcentral/${img}:latest YOUR_REGISTRY_HERE/${img}:latest
      docker push YOUR_REGISTRY_HERE/${img}:latest
    done
    ```

3. Replace the `ghcr.io/f5devcentral/...` image references in `nginx-declarative-api.yaml` with `YOUR_REGISTRY_HERE/...` and apply the manifest as shown in Option A.

## Publishing via Kubernetes Gateway API (`Gateway` & `HTTPRoute`)

`nginx-declarative-api.yaml` includes a commented-out **Kubernetes Gateway API (`gateway.networking.k8s.io/v1`)** configuration at the bottom of the file as an alternative to `Ingress` (for controllers such as F5 NGINX Gateway Fabric):

| Resource | Kind | Hostname (`spec.hostnames`) | Target Service & Port |
| --- | --- | --- | --- |
| `nginx-dapi-gateway` | `Gateway` | HTTP listener on port `80` (`gatewayClassName: nginx`) | Accepts routes from the `nginx-dapi` namespace |
| `nginx-dapi` | `HTTPRoute` | `nginx-dapi.k8s.example.com` | `nginx-dapi:5000` (`PathPrefix /`) |
| `webui` | `HTTPRoute` | `nginx-dapi-webui.k8s.example.com` | `webui:80` (`PathPrefix /`) |
| `mcp` | `HTTPRoute` | `nginx-dapi-mcp.k8s.example.com` | `mcp:8800` (`PathPrefix /`) |

To switch from `Ingress` to `Gateway` and `HTTPRoute`:

1. **Ensure Gateway API CRDs and a controller are installed** in your cluster (e.g., F5 NGINX Gateway Fabric with a `GatewayClass` named `nginx`, or update `gatewayClassName` to match your controller's `GatewayClass`).
2. **Comment out or remove the `Ingress` resource** in `nginx-declarative-api.yaml` to avoid duplicate hostname/routing conflicts.
3. **Uncomment the `Gateway` and `HTTPRoute` manifests** at the bottom of `nginx-declarative-api.yaml` and update `hostnames` for your DNS domain.
4. **Apply and verify** the Gateway API resources:

    ```shell
    kubectl apply -f nginx-declarative-api.yaml
    kubectl get gateway,httproute -n nginx-dapi
    ```

    Verify that `gateway/nginx-dapi-gateway` reports `PROGRAMMED: True` with an external address assigned, and all three `HTTPRoute` resources are accepted by the `http` listener.

## How to Undeploy

Delete the resources created by `nginx-declarative-api.yaml`:

```shell
kubectl delete -f nginx-declarative-api.yaml
```
