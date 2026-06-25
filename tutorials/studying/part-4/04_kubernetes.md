---
technologies: "Kubernetes"
category: "Explanation and use of technology"
difficulty: "Easy"
---

# Kubernetes

## Used material

1. <span id="used-material-1"></span> [Kubernetes Overview](https://kubernetes.io/docs/concepts/overview/)

2. <span id="used-material-2"></span> [Command line tool (kubectl)](https://kubernetes.io/docs/reference/kubectl/)

3. <span id="used-material-3"></span> [Kubernetes Python client Github](https://github.com/kubernetes-client/python)

4. <span id="used-material-4"></span> [Kubernetes documentation](https://kubernetes.io/docs/home/)

5. <span id="used-material-5"></span> [Kubernetes pods](https://kubernetes.io/docs/concepts/workloads/pods/)

6. <span id="used-material-6"></span> [Kubectl Quick Reference](https://kubernetes.io/docs/reference/kubectl/quick-reference/)

## Why use Kubernetes?

Kubernetes is widely used for the following reasons:

- The most common orchestration tool for cloud environments (mature)

- Enables easy to setup a wide range of software (abstracted)

- Usable in any place that supports Docker (interoperable)

These make Kubernetes the default container orchestrator for cloud environments, enabling us to develop, test, and run a wide range of software stacks.

## How to use Kubernetes?

We will interact with Kubernetes [(1)](#used-material-1) only through kubectl [(2)](#used-material-2) and in the future chapters, Python software client [(3)](#used-material-3), which is why you should check [(4)](#used-material-4) when necessary. You should also check the definition of a pod using [(5)](#used-material-5). The most important kubectl commands for our use case are [(6)](#used-material-6):

- Get cluster information

```
kubectl describe nodes
```

- Apply the YAML file

```
kubectl apply -f (YAML_file_path)
```

- Delete the effects of the YAML file

```
kubectl delete -f (YAML_file_path)
```

- Get pods from all namespaces

```
kubectl get pods -A
```

- Get services from all namespaces

```
kubectl get services -A
```

- Get a Kubernetes resource from a specific namespace

```
kubectl get (object_name) -n (namespace)
```

- Get pod logs

```
kubect logs (pod_name) -n (namespace)
```

- Get pod details

```
kubectl describe pod (pod_name) -n (namespace)
```

- Get inside a pod

```
kubectl exec -it (pod_name) -- /bin/bash
```

- Delete pod

```
kubectl delete pod (pod_name) -n (namespace)
```

Be aware that there are many useful commands, and that any problems Kubernetes faces can be solved either by waiting, debugging the YAML files used to deploy pods, or deleting faulty Kubernetes resources.

## Important parts of Kubernetes

The most important parts to keep an eye on when using Kubernetes to run containers are:

- Deployment YAMLs = The files that enable Kubernetes to run the pod

- Cluster resources = The compute Kubernetes can reserve to run the pods

- Pod logs = The print the software run in the pod gives during execution

- Pod describe = The details Kubernetes knows about the pod

- Resource effects = The expected effects of a Kubernetes resource on the cluster

---