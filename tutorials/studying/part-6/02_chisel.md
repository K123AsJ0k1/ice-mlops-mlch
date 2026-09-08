---
technologies: "Chisel"
category: "Choice and use of technology"
difficulty: "Intermediate"
---

# Chisel

## Used material

1. <span id="used-material-1"></span> [Chisel github](https://github.com/jpillora/chisel)

2. <span id="used-material-2"></span> [Secure Gateways](https://istio.io/latest/docs/tasks/traffic-management/ingress/secure-ingress/)

## Why use Chisel?

Chisel is a common secure TCP/UDP tunnel tool for the following reasons:

- Provides a single binary, production-grade tunneling over HTTP with a resilient connection lifecycle (mature)

- Easy way to provide network topology decoupling between separated networks with container native integration and port range multiplexing (abstracted)

- Widely supported by different operating systems with various security options and ability to traverse networks with different firewall configurations (interoperable)

These make Chisel the default interaction bridge between local and cloud environments, enabling separated services to interact and create distributed workflows.

## How to use Chisel?

Assuming you have setup Kind platform networking in the [Istio chapter](../part-4/11_istio.md), we can use it with Chisel to create a HTTPS Istio network gateway |[(1)](#used-material-1), [(2)](#used-material-2)| that enables connecting local and cloud Ray clusters described in the [Ray chapter](./01_ray.md) into the OSS MLOps platform. These connections will remotely forward the cluster dashboard and serve ports, while local forwarding will run useful services on the OSS MLOps platform. We can do this in the following steps:

1. Define the ports used for chisel, local clusters, and cloud clusters. In our case, we use:

- Chisel
    - Network
        - Control = 8080
- Local clusters
    - Laptop 1
        - Dashboard = 8100
        - Serve = 8301
    - Laptop 2
        - Dashboard = 8101
        - Serve = 8302
    - Laptop 3
        - Dashboard = 8103
        - Serve = 8303
- Cloud clusters
    - Virtual machine 2
        - Dashboard = 8401
        - Serve = 8401

2. Deploy a Chisel server on the OSS platform. See the example [deployment](./deployments/chisel/chisel-deployment.yaml) and [service](./deployments/chisel/chisel-service.yaml). 

```
cd ice-mlops-mlch/tutorials/studying/part-6/deployments
kubectl apply -k chisel
```

3. Modify Istio Ingress Gateway to have a port for Chisel.

```
cd ice-mlops-mlch/tutorials/studying/part-6/deployments
kubectl get svc istio-ingressgateway -n istio-system -o yaml > chisel-istio-ingressgateway.yaml
nano chisel-istio-ingressgateway.yaml
```

Edit the YAML spec-ports to have the following:

```
- name: chisel-https
  nodePort: 31008
  port: 206 
  protocol: TCP
  targetPort: 9007
```

Save it and apply it with:

```
CTRL + X 
Y
kubectl apply -f chisel-istio-ingressgateway.yaml
```

4. Create an HTTPS certificate on your main local development machine.

```
openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 \
  -subj '/O=OSS Platform/CN=oss-istio' \
  -keyout oss_platform_ca.key -out oss_platform_ca.crt

openssl req -newkey rsa:2048 -nodes \
  -subj "/O=OSS Platform/CN=chisel.oss" \
  -keyout oss_chisel_server.key -out oss_chisel_server.csr

openssl x509 -req -sha256 -days 365 -set_serial 0 \
  -CA oss_platform_ca.crt -CAkey oss_platform_ca.key \
  -in oss_chisel_server.csr -out oss_chisel_server.crt \
  -extfile <(printf "subjectAltName=DNS:chisel.oss")
```

5. Transfer the generated .key and .crt files to the virtual machine running the OSS MLOPs platform.

```
mkdir certificates
cat oss_chisel_server.(key/crt)
SHIFT + CTRL + C
nano oss_chisel_server.(key/crt)
SHIFT + CTRL + V
CTRL + X
Y
```

6. Create the TLS secret using these keys.

```
kubectl create secret tls chisel-credential \
  --key=oss_chisel_server.key \
  --cert=oss_chisel_server.crt \
  -n istio-system
```

7. Create a Chisel gateway and virtual service. See the example [gateway](./deployments/istio/chisel/chisel-gateway.yaml) and [virtualservice](./deployments/istio/chisel/chisel-virtualservice.yaml).

```
cd ice-mlops-mlch/tutorials/studying/part-6/deployments
kubectl apply -k istio
```

8. Modify the virtual machine firewalls to have TCP with port range 7008 and remote IP prefix 0.0.0.0

9. Test the connection to Chisel from your development computer. See example [response](./deployments/responses/chisel-curl.txt)

```
curl -v --cacert oss_platform_ca.crt --resolve "chisel.oss:7008:[VM_PUBLIC_IP]" "https://chisel.oss:7008"
```

10. Update the virtual services of local and cloud ray clusters to point toward chisel server. See example [dasbhoard](./deployments/istio/ray/dashboard/ray-cloud-2-virtualservice.yaml) and [serve](./deployments/istio/ray/serve/ray-cloud-2-virtualservice.yaml).

11. Consider the OSS platform services you want to make accessible to the Ray clusters. In our case, they are:

- Mlflow 
    - Cluster address = mlflow.mlflow.svc.cluster.local:5000
- MLflow MinIO
    - Cluster address = mlflow-minio-service.mlflow.svc.cluster.local:9000
- MinIO
    - Cluster address = minio-service.storage.svc.cluster.local:9100
- MongoDB
    - Cluster address = mongo-service.storage.svc.cluster.local:27017
- Neo4j
    - Cluster address = neo4j-service.storage.svc.cluster.local:7687
- Qdrant
    - Cluster address = qdrant-service.storage.svc.cluster.local:7201
- Redis
    - Cluster address = redis-service.storage.svc.cluster.local:6379

12. Modify the local and cloud Ray cluster compose YAMLs to include the Chisel client. See example [YAML](./deployments/ray/local-cloud-compose-ray-cluster-with-chisel.yaml). In the YAML, we see the following commands:

```
client 
--auth chisel1234:chisel4567 
--tls-ca /run/secrets/cpouta-oss-crt 
https://chisel.oss:7008 
R:0.0.0.0:8401:ray-head:8265
R:0.0.0.0:8451:ray-head:8350
0.0.0.0:5000:mlflow.mlflow.svc.cluster.local:5000
0.0.0.0:9000:mlflow-minio-service.mlflow.svc.cluster.local:9000
0.0.0.0:9100:minio-service.storage.svc.cluster.local:9100
0.0.0.0:27017:mongo-service.storage.svc.cluster.local:27017
0.0.0.0:7687:neo4j-service.storage.svc.cluster.local:7687
0.0.0.0:7201:qdrant-service.storage.svc.cluster.local:7201
0.0.0.0:6379:redis-service.storage.svc.cluster.local:6379
```

For comparison, here are the server commands:

```
args:
- "server"
- "--port"
- "8080" 
- "--auth"
- "chisel1234:chisel4567"
- "--reverse"
```

These commands enable Istio to handle TLS by inspecting the traffic it receives. This traffic contains the .crt file provided by the compose secret, which allows Istio to let the traffic continue to the chisel server. 

When it arrives at the server, the server checks whether the traffic authentication matches what was provided, which then lets the client connect and ask the server to remote-forward the Ray cluster dashboard and serve address, while locally forwarding the desired services.

13. Make the cluster run to confirm that everything works. See example [compose logs](./deployments/logs/local-cloud-ray-cluster-with-chisel-logs.txt).

```
cd ice-mlops-mlch/tutorials/studying/part-6/deployments/ray
docker compose -f local-cloud-compose-ray-cluster-with-chisel.yaml
```

14. You can further confirm by checking server logs. See example [kubectl logs](./deployments/logs/kubectl-chisel-server-logs.txt)

```
kubectl get pods -n chisle
kubectl logs chisel-server-(identity) -n chisel
```

15. If the logs show no problems, you should now be able to utilize the local and cloud ray clusters. For our case they have following addresses:

- Local clusters
    - Laptop 1
        - Dashboard = http://ray.local.dash-1.oss
        - Serve = http://ray.local.serve-1.oss
    - Laptop 2
        - Dashboard = http://ray.local.dash-2.oss
        - Serve = http://ray.local.serve-2.oss
    - Laptop 3
        - Dashboard = http://ray.local.dash-3.oss
        - Serve = http://ray.local.serve-3.oss
- Cloud clusters
    - Virtual machine 2
        - Dashboard = http://ray.cloud.dash-2.oss
        - Serve = http://ray.cloud.serve-2.oss

This gives us a key networking component that connects multiple local and cloud Ray clusters into a centralized network for local-cloud MLOps workflows. You can use it as-is to connect new computers by setting up Docker and providing the .crt file, or enhance it for complex networking use cases such as individualized network access or connecting multiple separate OSS clusters. For our use case, we will utilize the current form later.

---