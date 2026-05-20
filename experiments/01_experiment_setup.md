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
cd applications/packages/icebreaker
pip install -e ".[all]"
```
