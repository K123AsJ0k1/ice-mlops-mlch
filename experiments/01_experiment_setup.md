# Experiment setup

This document shows how we setup things for the experiments. It assumes the following

- The calculations can be done with Python, pip and Ray
- Multiple laptops running docker desktop
- Some of the laptops have GPUs with atleast 8GB VRAM
- The laptop GPUs can be used by docker desktop
- MyCSC account with SSH keys
- Two MyCSC projects (regular and LUMI)
- Access to CSC CPouta
- Atleast 2 CPouta virtual machines with docker engines
- All virtual machines use volumes for docker 
- One of the CPouta VMs has a GPU
- GPU VM has working drivers, CUDA and container toolkit
- Access to CSC Allas
- Access to multiple CSC HPC platforms (puhti, mahti and LUMI)
- SLURM Ray can be run in the HPC platform

## Available infrastructure

In our case the available resources provided by our local and cloud infrastructure with a 2 CPU and 2GB deduction to ensure stability are:

- Local
    - Laptop 1 (central)
        - Docker desktop compose ray cluster
        - OS: Ubuntu 24.04
        - Ray resources
            - CPUs = 12 from 14
            - RAM = 12GB from 14.63GiB
            - GPUs = 0
    - Laptop 2
        - Docker desktop compose ray cluster
        - OS: Windows 11 with WSL2
        - Ray resources
            - CPUs = 14 from 16
            - RAM = 10 GB from 11.53GiB (docker restrained from 23.7 GT)
            - GPUs = 1 NVIDIA GeForce RTX 4070 8188 MIB
    - Laptop 3
        - Docker desktop compose ray cluster
        - OS: Windows 11 with WSL2
        - Ray resources
            - CPUs = 30 from 32
            - RAM = 14GB from 15.49GIB (docker restrained from 31.7 GT)
            - GPUs = 1 NVIDIA GeForce RTX 4090 16376MIB
    - Local ray resources
        - CPUs = 56
        - RAM = 36 GB
        - GPUs = 2 with 24 564 MIB
            - NVIDIA GeForce RTX 4070
            - NVIDIA GeForce RTX 4090   
- Cloud
    - Virtual machine 1 (central)
        - Kind docker engine kuberay cluster
        - OS: Ubuntu 22.04.5 LTS
        - Available docker resources
            - CPUs = 8 of 14 (4925m in use)
            - RAM = 104GB from 115.1GiB (9129780480 aka 8G aka 8.057 in use)
            - GPUs = 1 NVIDIA Tesla P100 16381MIB
    - Virtual machine 2
        - Docker engine compose ray cluster
        - OS: Ubuntu 22.04.5 LTS
        - Available docker resources
            - CPUs = 6 of 8
            - RAM = 28GB of 30.6GIB
            - GPUs = 0
    - Cloud ray resources
        - CPUs = 14
        - RAM = 128 GB
        - GPUs = 1 with 16381MIB
            - NVIDIA Tesla P100

This means the collective resources provided by local-cloud ray clusters are:

- CPUs = 84
- RAM = 187,35 GIB
- GPUs = 3 with 40 945 MIB
    - NVIDIA GeForce RTX 4070 8188 MIB
    - NVIDIA GeForce RTX 4090 16376MIB
    - NVIDIA Tesla P100 16381MIB

For fairness, we will try to reserve same amount of CPU and GPU resources with sensible amount of RAM in HPC as provided by local infrastructure:

- Puhti
    - partition = gpu
    - Nodes = 2 (head-worker)
    - CPU = 8 (max 10 per GPU)
    - RAM = 16 GB
    - GPU = 1 (NVIDIA V100 32 GB)
- Mahti
    - partition = gpumedium
    - Nodes = 2 (head-worker)
    - CPU = 30 (max 32 per GPU)
    - RAM = 60 GB
    - GPU = 1 (NVIDIA A100 80 GB)
- LUMI 
    - partition = small
    - Nodes = 2 (head-worker)
    - CPU = 16
    - RAM = 32 GB
    - GPU = 0

## Python and Ray versions

The Python and Ray versions have differences between enviroments with HPC platforms setting the constraints. Since we have better control over local and cloud, we will use the following versions:

- Local
    - Laptop 1
        - Python: 3.12.3
        - Ray: 2.49.2-py312-cpu
    - Laptop 2
        - Python: 3.12.3
        - Ray: 2.49.2-py312-cu128 
    - Laptop 3
        - Python: 3.12.3
        - Ray: 2.49.2-py312-cu128
- Cloud
    - Virtual machine 1
        - Python: 3.10.12
        - Ray: 2.49.2-py312-cu121
    - Virtual machine 2
        - Python: 3.10.12
        - Ray: 2.49.2-py312-cpu
- HPC
    - Puhti
        - Python: 3.12.12 (pytorch/2.7 module)
        - Ray: 2.47.1  (pytorch/2.7 module)
    - Mahti
        - Python: 3.12.12 (pytorch/2.7 module)
        - Ray: 2.47.1  (pytorch/2.7 module)
    - LUMI:
        - Python: 3.11.0rc1 (pytorch/2.7 module)
        - Ray: 2.44.1 (pytorch/2.7 module)

## Setup

### Local Development enviroment

1. Create a python virtual enviroment

```
python3 -m venv exp_venv
```

2. Activate the enviroment

```
source exp_venv/bin/activate
```

3. Install jupyter lab

```
pip install -r packages.txt
```

4. Install repository package 

```
cd ..
cd applications/packages/icebreaker
pip install -e ".[all]"
```

If there are problems, you can uninstall the package to fix it with

```
pip uninstall icebreaker
```

### Local-cloud-HPC OSS 

The OSS MLOps platform was setup in the following way:

1. Confirm your docker engine works

```
docker info
```

2. Check that nvidia-smi works

```
nvidia-smi
```

3. Clone the OSS repository and run the setup script

```
git clone git@github.com:K123AsJ0k1/multi-cloud-hpc-oss-mlops-platform.git
cd multi-cloud-hpc-oss-mlops-platform
chmod +x integration-setup.sh
./integration-setup.sh
```

2. Give these options

```
Setup integration (y/n) (default is [n]): y

Please choose the deployment option:
[1] Kubeflow (all components)
[2] Kubeflow (some components removed)
[3] Standalone KFP
[4] Standalone KFP and Kserve
Enter the number of your choice [1-4] (default is [1]): 3

Install local Docker registry? (y/n) (default is [y]): y

Setup GPU Cluster (Requires atleast 1 GPU) (y/n) (default is [n]): y

Install Ray? (It requires ~4 additional CPUs) (y/n) (default is [n]): n
```

3. After the setup in complete, check that all pods are running (might need 20 mins)

```
kubectl get pods -A
```

4. Run nvshare tests

```
kubectl apply -f https://raw.githubusercontent.com/grgalex/nvshare/main/tests/kubernetes/manifests/nvshare-tf-pod-1.yaml && \
kubectl apply -f https://raw.githubusercontent.com/grgalex/nvshare/main/tests/kubernetes/manifests/nvshare-tf-pod-2.yaml
```

5. Confirm that GPU is being used

```
nvidia-smi
```

6. Confirm that tests passed

```
kubectl logs nvshare-tf-matmul-1 -f

kubectl logs nvshare-tf-matmul-2 -f
```

7. Deploy Kuberay (fix path in the future)

```
cd multi-cloud-hpc-oss-mlops-platform/experiments/deployments/ray
helm repo add kuberay https://ray-project.github.io/kuberay-helm/
helm repo update
helm install kuberay-operator kuberay/kuberay-operator --version 1.0.0
helm install raycluster kuberay/ray-cluster --version 1.0.0 -f cloud-vm-1-kuberay-values.yaml
```

8. Confirm that ray head and worker are running

```
kubectl get pods
```

9. Check the ray head and worker logs

```
kubectl logs raycluster-kuberay-head-() -n default
kubectl logs raycluster-kuberay-worker-() -n default
```

8. Deploy Apache Airflow (Will take a moment. Maybe this should be done in the setup script or atleast fix path in the future) 

```
(assuming the forwarder postres is running)
cd multi-cloud-hpc-oss-mlops-platform/integration/forwarder/airflow
helm repo add apache-airflow https://airflow.apache.org
helm upgrade --install airflow apache-airflow/airflow --namespace forwarder -f apache-airflow-values.yaml
```

9. Deploy storages  (fix path in the future)

```
cd multi-cloud-hpc-oss-mlops-platform/tutorials/integration/studying/parts/part-4/kustomize
kubectl apply -k storage
```

10. Deploy Ollama-Webui stack (fix path in the future)

```
cd multi-cloud-hpc-oss-mlops-platform/tutorials/integration/studying/parts/part-4/kustomize
kubectl apply -k language
```

11. Configure istio (fix path in the future)

12. Configure SSH

13. Start controllers in local and cloud enviroments
