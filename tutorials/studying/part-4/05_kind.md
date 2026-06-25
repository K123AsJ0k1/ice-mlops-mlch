---
technologies: "Kubernetes in Docker"
category: "Explanation and use of technology"
difficulty: "Intermediate"
---

# Kubernetes in Docker

## Used material

1. <span id="used-material-1"></span> [Kind documentation](https://kind.sigs.k8s.io/)

2. <span id="used-material-2"></span> [Configuration](https://kind.sigs.k8s.io/docs/user/configuration/)

3. <span id="used-material-3"></span> [K8s Kind with GPUs](https://web.archive.org/web/20240415022820/https://www.substratus.ai/blog/kind-with-gpus)

4. <span id="used-material-4"></span> [Adding GPU support to kind](https://jacobtomlinson.dev/posts/2022/quick-hack-adding-gpu-support-to-kind/)

5. <span id="used-material-5"></span> [Installing the NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/getting-started.html)

6. <span id="used-material-6"></span> [K8s-device-plugin Github](https://github.com/NVIDIA/k8s-device-plugin)

7. <span id="used-material-7"></span> [Nvshare GitHub](https://github.com/grgalex/nvshare?tab=readme-ov-file#deploy_k8s)

8. <span id="used-material-9"></span> [Kubernetes NodePort](https://www.tkng.io/services/nodeport/)

9. <span id="used-material-9"></span> [Docker Port publishing and mapping](https://docs.docker.com/engine/network/port-publishing/)

## Why use Kubernetes in Docker?

Kubernetes in Docker (Kind) is used for the following reasons:

- A common tool for creating Kubernetes development environments (mature)

- Enables easy setup and development of Kubernetes containers (abstracted)

- Usable in any place that can run Docker (interoperable) 

These make Kind the default container environment for developing and running Kubernetes containers in cloud environments without native Kubernetes support. 

## How to use Kubernetes in Docker?

We will interact with kind only through setup scripts such as the [GPU cluster](bash/oss_create_gpu_cluster.sh) file, which is why check [(1)](#used-material-1) as necessary. In this script, the important row blocks are 14-161 and 166-309, which create the kind cluster with a specific configuration. 

If the resulting kind cluster is missing something, it is caused by incorrect or missing lines in the config text. Be aware that you need to recreate the cluster for the changes to take effect, which is why you should plan ahead for the desired configuration and confirm that you have already backed up all the data you want from the cluster.

## GPU configuration of Kubernetes in Docker

If we can use GPUs in Docker containers and we want to run GPU containers inside the kind cluster, we need to modify the extra mounts configuration [(2)](#used-material-2). This is done with the following steps |[(3)](#used-material-3), [(4)](#used-material-4), [(5)](#used-material-5), [(6)](#used-material-6)|:

1. Configure the NVIDIA runtime

```
sudo nvidia-ctk runtime configure --runtime=docker --set-as-default
sudo systemctl restart docker
sudo sed -i '/accept-nvidia-visible-devices-as-volume-mounts/c\accept-nvidia-visible-devices-as-volume-mounts = true' /etc/nvidia-container-runtime/config.toml
```

2. Add the following snippet:

```
extraMounts:
    - hostPath: /dev/null
        containerPath: /var/run/nvidia-container-devices/all
```

Once the cluster is running, we need to do the following steps to use the GPU:

1. Add [NVIDIA GPU Operator](./bash/oss_install_gpu_operator.sh)

```
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

helm install --generate-name \
     -n gpu-operator --create-namespace \
     nvidia/gpu-operator \
     --version=v24.9.0 \
     --set driver.enabled=false 
```

2. Create a YAML file with the following 

```
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod
spec:
  restartPolicy: Never
  containers:
    - name: cuda-container
      image: nvcr.io/nvidia/k8s/cuda-sample:vectoradd-cuda10.2
      resources:
        limits:
          nvidia.com/gpu: 1
  tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule
```

3. Run the test

```
kubectl apply -f gpu-test.yaml
```

4. Check the received logs

```
kubectl logs gpu-pod
```

5. Confirm that the test passed

```
[Vector addition of 50000 elements]
Copy input data from the host memory to the CUDA device
CUDA kernel launch with 196 blocks of 256 threads
Copy output data from the CUDA device to the host memory
Test PASSED
Done
```

6. Add [Nvshare](./bash/oss_install_gpu_nvshare.sh)

```
kubectl apply -f https://raw.githubusercontent.com/grgalex/nvshare/main/kubernetes/manifests/nvshare-system.yaml && \
kubectl apply -f https://raw.githubusercontent.com/grgalex/nvshare/main/kubernetes/manifests/nvshare-system-quotas.yaml && \
kubectl apply -f https://raw.githubusercontent.com/grgalex/nvshare/main/kubernetes/manifests/device-plugin.yaml && \
kubectl apply -f https://raw.githubusercontent.com/grgalex/nvshare/main/kubernetes/manifests/scheduler.yaml
```

7. Confirm it runs

```
kubectl get pods -n nvshare-system
```

8. Run tests

```
kubectl apply -f https://raw.githubusercontent.com/grgalex/nvshare/main/tests/kubernetes/manifests/nvshare-tf-pod-1.yaml && \
kubectl apply -f https://raw.githubusercontent.com/grgalex/nvshare/main/tests/kubernetes/manifests/nvshare-tf-pod-2.yaml
```

9. Check logs


```
kubectl logs nvshare-tf-matmul-1 -f
kubectl logs nvshare-tf-matmul-2 -f
```

10. Confirm that the tests passed

```
PASS
--- 217.63522791862488 seconds ---
PASS
--- 228.7243537902832 seconds  ---
```

Now, we can use GPUs inside Kind and use the same GPU between 10 containers by adding the following to their YAML files:

```
resources:
  limits:
    nvshare.com/gpu: 1
```

Be aware that if for some reason GPU pods are failing or Nvshare is having problems such as:

```
[NVSHARE][INFO]: nvshare-scheduler started in normal mode
[NVSHARE][INFO]: Error deleting existing socket `/var/run/nvshare/scheduler.sock'
[NVSHARE][FATAL]: Condition failed: nvshare_bind_and_listen(&lsock, nvscheduler_socket_path) == 0
```

It might be caused by NvShare misconfiguration or a VM update. The steps to fix this are:

1. Delete containers that use Nvshare

2. Delete Nvshare 

```
kubectl delete -f https://raw.githubusercontent.com/grgalex/nvshare/main/kubernetes/manifests/scheduler.yaml
kubectl delete -f https://raw.githubusercontent.com/grgalex/nvshare/main/kubernetes/manifests/device-plugin.yaml && \
kubectl delete -f https://raw.githubusercontent.com/grgalex/nvshare/main/kubernetes/manifests/nvshare-system-quotas.yaml && \
kubectl delete -f https://raw.githubusercontent.com/grgalex/nvshare/main/kubernetes/manifests/nvshare-system.yaml
```

3. Install Nvshare with step 6

4. Remove old test pods

```
kubectl delete pod nvshare-tf-matmul-1
kubectl delete pod nvshare-tf-matmul-2
```

4. Rerun tests with step 8.

5. If that does work, delete Nvshare again and reboot VM 

```
sudo reboot
```

4. When the cluster is running, add Nvshare back with step 6.

## Port configuration of Kubernetes in Docker

If we want to interact directly with the containers running in the kind cluster, we need to modify extraPortMappings [(2)](#used-material-2). We can do this by adding more entries to extraPortMappings in the following way:

```
extraPortMappings:
  - containerPort: 31001
    hostPort: 7001
    protocol: TCP
  - containerPort: 31002
    hostPort: 7002
    protocol: TCP
  - containerPort: 31003
    hostPort: 7003
    protocol: TCP
  - containerPort: 31004
    hostPort: 7004
    protocol: TCP
```

Here, containerPort is in the Kubernetes NodePort [(8)](#used-material-8) range, 30000-32767, and hostPort is a port opened by Docker [(9)](#used-material-9). We will later use this to enable us to send requests to containers through a service mesh from outside the Kind Cluster

---