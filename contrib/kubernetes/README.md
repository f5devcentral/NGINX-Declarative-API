# Running NGINX Declarative API on Kubernetes

NGINX Declarative API can be deployed on Kubernetes using the manifest provided

## How to deploy

1. Build the NGINX Declarative API docker images using the [Docker-compose script](/contrib/docker-compose)

2. Tag and push the docker images to a private registry

    ```shell
    docker tag nginx-declarative-api:latest YOUR_REGISTRY_HERE/nginx-declarative-api:latest
    docker push YOUR_REGISTRY_HERE/nginx-declarative-api:latest

    docker tag nginx-declarative-api-devportal:latest YOUR_REGISTRY_HERE/nginx-declarative-api-devportal:latest
    docker push YOUR_REGISTRY_HERE/nginx-declarative-api-devportal:latest
    ```

3. Edit `nginx-declarative-api.yaml` and update the following lines to match the docker images and to set the `Ingress` host DNS name

    ```shell
            image: YOUR_REGISTRY_HERE/nginx-declarative-api:latest
            image: YOUR_REGISTRY_HERE/nginx-declarative-api-devportal:latest
            image: YOUR_REGISTRY_HERE/nginx-declarative-api-webui:latest
    ```

    ```shell
        - host: nginx-dapi.k8s.f5.ff.lan
        - host: nginx-dapi-webui.k8s.f5.ff.lan
    ```

4. Apply the manifest

    ```shell
    $ kubectl apply -f nginx-declarative-api.yaml 
    namespace/nginx-dapi created
    deployment.apps/redis created
    deployment.apps/nginx-dapi created
    deployment.apps/devportal created
    deployment.apps/webui created
    service/redis created
    service/nginx-dapi created
    service/devportal created
    service/webui created
    ingress.networking.k8s.io/nginx-dapi created
    ```

5. Make sure all pods are up and running

    ```shell
    $ kubectl get all -n nginx-dapi
    NAME                              READY   STATUS    RESTARTS      AGE
    pod/devportal-74fc5c9ccb-5wjpr    1/1     Running   0             25s
    pod/nginx-dapi-848599b79b-ll2kg   1/1     Running   0             25s
    pod/redis-5cdb78b899-hjz9x        1/1     Running   0             25s
    pod/webui-2edc85a732-jrg8p        1/1     Running   0             25s
    ```

6. The NGINX Declarative API can be accessed through its `Ingress` resource

    ```shell
    $ kubectl get ingress -n nginx-dapi
    NAME         CLASS   HOSTS                      ADDRESS   PORTS   AGE
    nginx-dapi   nginx   nginx-dapi.k8s.f5.ff.lan             80      34s
    nginx-dapi   nginx   nginx-dapi-webui.k8s.f5.ff.lan       80      34s
    ```

## How to undeploy

1. Delete the `nginx-declarative-api.yaml` manifest

    ```shell
    kubectl delete -f nginx-declarative-api.yaml
    ```
