---
technologies: "Kustomize"
category: "Explanation and use of technology"
difficulty: "Intermediate"
---

# Kustomize

## Used material

1. <span id="used-material-1"></span> [Kustomize](https://kustomize.io/)

2. <span id="used-material-2"></span> [Declarative Management of Kubernetes Objects Using Kustomize](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/)

3. <span id="used-material-3"></span> [Kubernets deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)

4. <span id="used-material-4"></span> [Kubernetes service](https://kubernetes.io/docs/concepts/services-networking/service/)

5. <span id="used-material-5"></span> [Kubernetes namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)

6. <span id="used-material-6"></span> [Kubernetes secret](https://kubernetes.io/docs/concepts/configuration/secret/)

7. <span id="used-material-7"></span> [Kubernetes volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)

8. <span id="used-material-8"></span> [Kubernetes enviromental variables](https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/)

9. <span id="used-material-9"></span> [Kubernetes ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)

10. <span id="used-material-10"></span>[Managing Secrets using Kustomize](https://kubernetes.io/docs/tasks/configmap-secret/managing-secret-using-kustomize/)

11. <span id="used-material-11"></span> [Redis GitHub](https://github.com/redis/redis)

12. <span id="used-material-12"></span> [MinIO GitHub](https://github.com/minio/minio)

13. <span id="used-material-13"></span> [Postgres GitHub](https://github.com/postgres/postgres)

14. <span id="used-material-14"></span> [MongoDB GitHub](https://github.com/mongodb/mongo)

15. <span id="used-material-15"></span> [MongoExpress GitHub](https://github.com/mongo-express/mongo-express)

16. <span id="used-material-16"></span> [Qdrant GitHub](https://github.com/qdrant/qdrant)

17. <span id="used-material-17"></span> [Neo4j GitHub](https://github.com/neo4j/neo4j)

18. <span id="used-material-18"></span> [Kubernetes Use Port Forwarding to Access Applications in a Cluster](https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/)

## Why use Kustomize?

Kustomize is widely used for the following reasons:

- The most common tool for applying Kubernetes YAML templates (mature)

- Enables easy creation and setup of complex Kubernetes software deployments (abstracted)

- Usable in any Kubernetes cluster (interoperable)

These make Kustomize the default configuration manager for Kubernetes, enabling us to create complex container deployments that we can easily deploy and modify.

## How to use Kustomize?

Assuming we have a running OSS MLOps platform setup in the [OSS chapter](./06_oss_mlops_platform.md), we can start using Kustomize [(1)](#used-material-1) by deploying a provided [storage deployment](./kustomize/storage/kustomization.yaml) created with |[(2)](#used-material-2), [(3)](#used-material-3), [(4)](#used-material-4), [(5)](#used-material-5), [(6)](#used-material-6), [(7)](#used-material-7), [(8)](#used-material-8), [(9)](#used-material-9)|. It will deploy Redis [(11)](#used-material-11), MinIO [(12)](#used-material-12), Postgres [(13)](#used-material-13), MongoDB [(14)](#used-material-14), MongoExpress [(15)](#used-material-15), Qdrant [(16)](#used-material-16), and Neo4j [(17)](#used-material-17) to provide caching, object, relational, structured, vector, and graph databases. We can deploy them by running the following command:

```
cd multi-cloud-hpc-oss-mlops-platform/tutorials/integration/studying/parts/part-4/kustomize
kubectl apply -k storage
```

You can confirm that they work by comparing the logs and describe of their pods against the given ones:

- Redis [logs](./misc/redis-logs.txt) and [describe](./misc/redis-describe.txt)

- MinIO [logs](./misc/minio-logs.txt) and [describe](./misc/minio-describe.txt)

- Postgres [logs](./misc/postgres-logs.txt) and [describe](./misc/postgres-describe.txt)

- MongoDB frontend [logs](./misc/express-logs.txt) and [describe](./misc/express-describe.txt)

- MongoDB backend [logs](./misc/mongo-logs.txt) and [describe](./misc/mongo-describe.txt)

- Qdrant [logs](./misc/qdrant-logs.txt) and [describe](./misc/qdrant-describe.txt)

- Neo4j [logs](./misc/neo4j-logs.txt) and [describe](./misc/neo4j-describe.txt)

We can get access to them as mentioned in the [SSH chapter](./01_ssh.md) in the following way [(18)](#used-material-18):

```
# Redis
ssh -L 6379:localhost:6379 cpouta
kubectl port-forward svc/redis-service 6379:6379 -n storage

# MinIo backend
ssh -L 9100:localhost:9100 cpouta
kubectl port-forward svc/minio-service 9100:9100 -n storage

# MinIO frontend
ssh -L 9101:localhost:9101 cpouta
kubectl port-forward svc/minio-service 9101:9101 -n storage (user is minioadmin and password is minioadmin)

# Postgresql
ssh -L 5532:localhost:5532 cpouta
kubectl port-forward svc/postgres-service 5532:5532 -n storage

# Mongo frontend
ssh -L 7200:localhost:7200 cpouta
kubectl port-forward svc/express-service 7200:7200 -n storage
http://localhost:7200 (user is express123 and password is express456)

# Mongo backend
ssh -L 27017:localhost:27017 cpouta
kubectl port-forward svc/mongo-service 27017:27017 -n storage
http://localhost:27017

# Qdrant
ssh -L 7201:localhost:7201 cpouta
kubectl port-forward svc/qdrant-service 7201:7201 -n storage
http://localhost:7201/dashboard (API key is qdrant_key)

# Neo4j frontend
ssh -L 7474:localhost:7474 cpouta
kubectl port-forward svc/neo4j-service 7474:7474 -n storage
http://localhost:7474 (user is neo4j, password is password)

# Neo4j backend (required for interactions)
ssh -L 7687:localhost:7687 cpouta
kubectl port-forward svc/neo4j-service 7687:7687 -n storage
http://localhost:7687
```

## Kustomize file structure

When you check the files inside the storage folder, you notice the following structure:

- [kustomization](./kustomize/storage/kustomization.yaml)
- [storage-namespace](./kustomize/storage/storage-namespace.yaml)
- [config](./kustomize/storage/config.env)
- [secret](./kustomize/storage/secret.env)
- cache
    - [kustomization](./kustomize/storage/cache/kustomization.yaml)
    - [redis-deployment](./kustomize/storage/cache/redis-deployment.yaml)
    - [redis-service](./kustomize/storage/cache/redis-service.yaml)
- objects
    - [kustomization](./kustomize/storage/objects/kustomization.yaml)
    - [minio-deployment](./kustomize/storage/objects/minio-deployment.yaml)
    - [minio-service](./kustomize/storage/objects/minio-service.yaml)
    - [minio-pvc](./kustomize/storage/objects/minio-pvc.yaml)
- relational
    - [kustomization](./kustomize/storage/relational/kustomization.yaml)
    - [postgres-deployment](./kustomize/storage/relational/postgres-deployment.yaml)
    - [postgres-service](./kustomize/storage/relational/postgres-pvc.yaml)
    - [postgres-config](./kustomize/storage/relational/postgres-config.yaml)
    - [postgres-pvc](./kustomize/storage/relational/postgres-pvc.yaml)
- sturctured
    - [kustomization](./kustomize/storage/structured/kustomization.yaml)
    - frontend
        - [kustomization](./kustomize/storage/structured/frontend/kustomization.yaml)
        - [express-deployment](./kustomize/storage/structured/frontend/express-deployment.yaml)
        - [express-service](./kustomize/storage/structured/frontend/express-service.yaml)
    - backend
        - [kustomization](./kustomize/storage/structured/backend/kustomization.yaml)
        - [mongo-deployment](./kustomize/storage/structured/backend/mongo-deployment.yaml)
        - [mongo-service](./kustomize/storage/structured/backend/mongo-service.yaml)
        - [mongo-pvc](./kustomize/storage/structured/backend/mongo-pvc.yaml)
- vectors
    - [kustomization](./kustomize/storage/vectors/kustomization.yaml)
    - [qdrant-deployment](./kustomize/storage/vectors/qdrant-deployment.yaml)
    - [qdrant-service](./kustomize/storage/vectors/qdrant-service.yaml)
    - [qdrant-pvc](./kustomize/storage/vectors/qdrant-pvc.yaml)
- graphs
    - [kustomization](./kustomize/storage/graphs/kustomization.yaml)
    - [neo4j-deployment](./kustomize/storage/graphs/neo4j-deployment.yaml)
    - [neo4j-service](./kustomize/storage/graphs/neo4j-service.yaml)
    - [neo4j-pvc](./kustomize/storage/graphs/neo4j-pvc.yaml)

The purpose of this structure is again easier understandability and development enabled by Kustomize, where each software has its own Kubernetes resources that we can invoke with a kustomization file, which itself is invoked by a kustomization file handling the whole stack.

## Important parts of Kustomize

The most important parts to keep an eye on when trying to understand or develop Kustomize configurations are:

- Main Kustomization = The root configuration file that points to folders, gives a namespace, and sets u variables

- Folder Kustomization = The branch configuration file that points to required Kubernetes resources 

- Resources = A list of necessary folders with kustomization or files for Kubernetes objects

- Namespace = A Kubernetes object that isolates resources in a single cluster

- Deployment = A Kubernetes object that defines the pod running the containers

- Service = A Kubernetes object that gives a network endpoint for the deployment

- PVC = A Kubernetes object that reserves disk memory for a deployment

- Config = Object that stores key-value pairs for deployment

- Generator = Automation tool for kubectl and kustomize that creates resources for deployment

---