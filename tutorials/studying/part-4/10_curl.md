---
technologies: "Curl"
category: "Explanation and use of technology"
difficulty: "Easy"
---

# Curl

## Used material

1. <span id="used-material-1"></span> [cURL Website](https://curl.se/)

2. <span id="used-material-2"></span> [Curl tutorial](https://curl.se/docs/tutorial.html)

3. <span id="used-material-3"></span> [Accessing a Kubernetes Pod and Service Using](https://medium.com/@jaberi.mohamedhabib/accessing-a-kubernetes-pod-and-service-using-curl-bb334393aa43)

4. <span id="used-material-4"></span> [Kubernetes DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)

5. <span id="used-material-5"></span> [Kubernetes Use Port Forwarding to Access Applications in a Cluster](https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/)

## Why use Curl?

Curl is widely used for the following reasons:

- Most common CLI for talking servers directly via URLs (mature)

- Easy to use to get data and send requests to servers (abstracted)

- Preinstalled to all major operating systems (interoperable)

These make Curl the default CLI data transfer tool for moving data and testing services. 

## How to use Curl?

We will use curl [(1)](#used-material-1) to test connections to OSS deployment services, so we will only show the relevant uses. Please check [(2)](#used-material-2) for details. Assuming we setup the databases in the [Kustomize chapter](./08_kustomize.md), we can test the networking inside the KinD cluster, outside the host in the VM, and outside the VM on our computer. We can test cluster networking with the following steps |[(3)](#used-material-3),[(4)](#used-material-4)|:

1. Deploy curl pod

```
cd multi-cloud-hpc-oss-mlops-platform/tutorials/integration/studying/parts/part-4/networking
kubectl apply -f curl-pod.yaml
```

2. Confirm it is running

```
kubectl get pods
```

3. Get the database services

```
kubectl get services -n storage
```

It should give the following print:

```
NAME               TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)             AGE
express-service    ClusterIP   10.96.81.187    <none>        7200/TCP            45h
minio-service      ClusterIP   10.96.90.243    <none>        9100/TCP,9101/TCP   45h
mongo-service      ClusterIP   10.96.103.4     <none>        27017/TCP           45h
neo4j-service      ClusterIP   10.96.124.106   <none>        7474/TCP,7687/TCP   45h
postgres-service   ClusterIP   10.96.163.121   <none>        5532/TCP            45h
qdrant-service     ClusterIP   10.96.244.55    <none>        7201/TCP            45h
redis-service      ClusterIP   10.96.182.100   <none>        6379/TCP            45h
```

4. Enter the pod

```
kubectl exec -it curl-pod -- /bin/sh
```

5. Send requests to (service-name).(service-namespace).svc.cluster.local:(service-port) with (-v) verbose flag

```
# redis
curl -v http://redis-service.storage.svc.cluster.local:6379

# MinIO client
curl -v http://minio-service.storage.svc.cluster.local:9100

# MinIO UI
curl -v http://minio-service.storage.svc.cluster.local:9101

# Postgres
curl -v http://postgres-service.storage.svc.cluster.local:5532

# Mongo Express
curl -v http://express-service.storage.svc.cluster.local:7200

# MongoDB
curl -v http://mongo-service.storage.svc.cluster.local:27017

# Qdrant
curl -v http://qdrant-service.storage.svc.cluster.local:7201

# Neo4j bolt
curl -v http://neo4j-service.storage.svc.cluster.local:7474

# Neo4j ui
curl -v http://neo4j-service.storage.svc.cluster.local:7687
```

6. Exit the pod

```
exit
```

7. Compare the prints against

- [Redis response](./networking/responses/redis-curl.txt)

- [MinIO client response](./networking/responses/minio-client-curl.txt)

- [MinIO UI response](./networking/responses/minio-ui-curl.txt)

- [Postgres response](./networking/responses/postgres-curl.txt)

- [Mongo Express response](./networking/responses/mongo-express-curl.txt)

- [MongoDB response](./networking/responses/mongo-db-curl.txt)

- [Qdrant response](./networking/responses/qdrant-curl.txt)

- [Neo4j Bolt response](./networking/responses/neo4j-bolt.txt)

- [Neo4j UI response](./networking/responses/neo4j-ui.txt)

These responses allow us to confirm if the networking we will setup to forward connections inside the cluster works. We can test port-forwarded connections inside the VM with the following steps [(5)](#used-material-5):

```
# redis
kubectl port-forward svc/redis-service 6379:6379 -n storage
curl -v http://localhost:6379

# MinIO client
kubectl port-forward svc/minio-service 9100:9100 -n storage
curl -v http://localhost:9100

# MinIO UI
kubectl port-forward svc/minio-service 9101:9101 -n storage
curl -v http://localhost:9101

# Postgres
kubectl port-forward svc/postgres-service 5532:5532 -n storage
curl -v http://localhost:5532

# Mongo Express
kubectl port-forward svc/express-service 7200:7200 -n storage
curl -v http://localhost:7200

# MongoDB
kubectl port-forward svc/mongo-service 27017:27017 -n storage
curl -v http://localhost:27017

# Qdrant
kubectl port-forward svc/neo4j-service 7201:7201 -n storage
curl -v http://localhost:7201

# Neo4j bolt
kubectl port-forward svc/neo4j-service 7474:7474 -n storage
curl -v http://localhost:7474

# Neo4j ui
kubectl port-forward svc/neo4j-service 7687:7687 -n storage
curl -v http://localhost:7687
```

The created curl responses should be the same as before. Finally, we can test all these connections on our own computer by ssh local forwarding them as shown in the [Kustomize chapter](./08_kustomize.md)

```
# redis
ssh -L 6379:localhost:6379 cpouta
kubectl port-forward svc/redis-service 6379:6379 -n storage
curl -v http://localhost:6379

# MinIO client
ssh -L 9100:localhost:9100 cpouta
kubectl port-forward svc/minio-service 9100:9100 -n storage
curl -v http://localhost:9100

# MinIO UI
ssh -L 9101:localhost:9101 cpouta
kubectl port-forward svc/minio-service 9101:9101 -n storage
curl -v http://localhost:9101

# Postgres
ssh -L 5532:localhost:5532 cpouta
kubectl port-forward svc/postgres-service 5532:5532 -n storage
curl -v http://localhost:5532

# Mongo Express
ssh -L 7200:localhost:7200 cpouta
kubectl port-forward svc/express-service 7200:7200 -n storage
curl -v http://localhost:7200

# MongoDB
ssh -L 27017:localhost:27017 cpouta
kubectl port-forward svc/mongo-service 27017:27017 -n storage
curl -v http://localhost:27017

# Qdrant
ssh -L 7201:localhost:7201 cpouta
kubectl port-forward svc/neo4j-service 7201:7201 -n storage
curl -v http://localhost:7201

# Neo4j bolt
ssh -L 7474:localhost:7474 cpouta
kubectl port-forward svc/neo4j-service 7474:7474 -n storage
curl -v http://localhost:7474

# Neo4j ui
ssh -L 7687:localhost:7687 cpouta
kubectl port-forward svc/neo4j-service 7687:7687 -n storage
curl -v http://localhost:7687
```

If the responses are the same as before, we have now confirmed that we can access the services on the cluster host and on our computer. Be aware that if curl, for some reason, cannot establish a connection, you might be missing a necessary flag, such as -H to provide metadata for service-mesh sorting or authentication. If curl can't establish a connection despite correct inputs, then either the service doesn't exist, or there is a network configuration error.

---