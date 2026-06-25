---
technologies: "OSS MLOps Platform"
category: "Choice and use of technology"
difficulty: "Easy"
---

# OSS MLOps Platform

## Used material

1. <span id="used-material-1"></span> [OSS MLOps Platform GitHub](https://github.com/OSS-MLOPS-PLATFORM/oss-mlops-platform)

## Why use OSS MLOps platform?

The open-source software (OSS) MLOps was chosen for the following reasons:

- It provides a good foundation with the necessary MLOps technologies (mature)

- Enables easy setup of a modular MLOps system (abstracted)

- Usable in any place that supports Docker (interoperable)

These enable us to use the OSS MLOps platform as a flexible environment for developing and maintaining MLOps that fits our use case. 

## How to use OSS MLOps platform?

Assuming that you have setup a VM with Docker Engine, we can setup the OSS MLOps platform to run in the following way:

```
git clone git@github.com:K123AsJ0k1/multi-cloud-hpc-oss-mlops-platform.git
cd multi-cloud-hpc-oss-mlops-platform
git checkout studying
chmod +x integration-setup.sh
./integration-setup.sh
```

You will be given options, where the recommendation for development is:

1. Setup integration = y

2. Please choose deployment option = 4

3. Install local Docker registry = y

4. Setup GPU cluster = n (y if you have GPUs)

5. Install Ray = n

The setup will be complete in around 5-15 mins. When the [setup](bash/oss_integration_setup.sh) script has completed, check the states of the cluster pods:

```
kubectl get pods -A
```

It will take a moment for the pod states to change into RUNNING. Be aware that in resource-constrained environments, some states may remain in PENDING because Kubernetes cannot provide the necessary resources. Remember that you can always check available cluster resources with:

```
kubectl describe nodes
```

You can find the resources by scrolling down to find similar to the following:

```
Resource           Requests         Limits
  --------           --------         ------
  cpu                5025m (35%)      26700m (190%)
  memory             9339495680 (7%)  22736Mi (19%)
  ephemeral-storage  0 (0%)           0 (0%)
  hugepages-1Gi      0 (0%)           0 (0%)
  hugepages-2Mi      0 (0%)           0 (0%)
  nvidia.com/gpu     1                1
  nvshare.com/gpu    0                0
```

Be aware that the amount of resources is decided by Docker, which you can check using the following command:

```
docker info
```

In our case, it shows the following relevant information:

```
Server:
 Containers: 2
  Running: 2
  Paused: 0
  Stopped: 0
 Images: 2
 Server Version: 29.3.0
 Storage Driver: overlay2
  Backing Filesystem: xfs
  Supports d_type: true
  Using metacopy: false
  Native Overlay Diff: true
  userxattr: false
 Discovered Devices:
  cdi: nvidia.com/gpu=0
  cdi: nvidia.com/gpu=GPU-f16021e1-47d4-fdab-f006-f8abd0d87558
  cdi: nvidia.com/gpu=all
 Runtimes: runc io.containerd.runc.v2 nvidia
 Default Runtime: nvidia
 Init Binary: docker-init
 containerd version: 301b2dac98f15c27117da5c8af12118a041a31d9
 runc version: v1.3.4-0-gd6d73eb8
 init version: de40ad0
 Kernel Version: 5.15.0-171-generic
 Operating System: Ubuntu 22.04.5 LTS
 OSType: linux
 Architecture: x86_64
 CPUs: 14
 Total Memory: 115.1GiB
 Name: gpu-oss-mlops-platform
 Docker Root Dir: /media/volume/docker
```

## Important parts of OSS MLOps platform

The most important parts to keep an eye on when developing and maintaining the OSS MLOps platform are:

- Host resources = The amount of resources given by the Docker engine

- Setup script = The main executable that automates cluster creation 

- Configuration scripts = The support executables that automate tool installation

- Kind cluster = The base that enables Kubernetes orchestration 

- Kubernetes deployments = The configuration files that setup the cluster tools

---