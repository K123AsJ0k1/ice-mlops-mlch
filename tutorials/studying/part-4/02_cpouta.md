---
technologies: "cPouta"
category: "Choice and use of technology"
difficulty: "Intermediate"
---

# cPouta

## Used material

1. <span id="used-material-1"></span> [cPouta](https://research.csc.fi/service/cpouta-community-cloud-service/)

2. <span id="used-material-2"></span> [Accounts](https://docs.csc.fi/accounts/)

3. <span id="used-material-3"></span> [Creating a new project](https://docs.csc.fi/accounts/how-to-create-new-project/)

4. <span id="used-material-4"></span> [Adding service access to a project](https://docs.csc.fi/accounts/how-to-add-service-access-for-project/)

5. <span id="used-material-5"></span> [Billing](https://docs.csc.fi/accounts/billing/)

6. <span id="used-material-6"></span> [Creating a virtual machine in Pouta](https://docs.csc.fi/cloud/pouta/launch-vm-from-web-gui/)

7. <span id="used-material-7"></span> [Virtual machine flavors and Billing Unit rates](https://docs.csc.fi/cloud/pouta/vm-flavors-and-billing/)

8. <span id="used-material-8"></span> [Managing service quotas](https://research.csc.fi/resources/quotas/)

9. <span id="used-material-9"></span> [Connecting to your virtual machine](https://docs.csc.fi/cloud/pouta/connecting-to-vm/)

10. <span id="used-material-10"></span> [Free IP address lookup tool](https://nordvpn.com/ip-lookup/)

11. <span id="used-material-11"></span> [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)

12. <span id="used-material-12"></span> [Linux post-installation steps for Docker Engine](https://docs.docker.com/engine/install/linux-postinstall/)

13. <span id="used-material-13"></span> [Persistent volumes](https://docs.csc.fi/cloud/pouta/persistent-volumes/)

14. <span id="used-material-14"></span> [VM lifecycle & saving Cloud BUs](https://docs.csc.fi/cloud/pouta/vm-lifecycle/)

15. <span id="used-material-15"></span> [Installing CUDA on Ubuntu 22.04 (RXT4080-laptop)](https://forums.developer.nvidia.com/t/installing-cuda-on-ubuntu-22-04-rxt4080-laptop/292899)

16. <span id="used-material-16"></span> [Installing the NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

17. <span id="used-material-17"></span> [A Practical Guide to Running NVIDIA GPUs on Kubernetes](https://www.jimangel.io/posts/nvidia-rtx-gpu-kubernetes-setup/)

## Why use cPouta?

The cPouta OpenStack cloud platform provided by the Center of Scientific Computing (CSC) is the easiest and fastest way to access cloud services for education and research in Finland [(1)](#used-material-1). OpenStack itself is widely used for the following reasons:

- One of the most common open source toolkits for setting up cloud infrastructures of any scale (mature)

- Enables easy cloud environment management via clients, CLI, and UI (abstracted)

- Widely supported for different hardware running on Linux systems (interoperable)

These enable us to use the CSC-run cPouta to create cloud virtual machines that either centralize management or provide additional resources, while offering synergistic benefits for other services provided by CSC.  

## How to use cPouta?

You need to create a MyCSC account [(2)](#used-material-2) and create a new project [(3)](#used-material-3) with cPouta access [(4)](#used-material-4) and billing units [(5)](#used-material-5). When you have gained access, follow [(6)](#used-material-6) to create the virtual machine (VM) with the following details [(7)](#used-material-7):

- Image = Ubuntu 22.04 or newer
- Flavor = standard.xxlarge 
    - CPU = 8
    - RAM = 31 GiB
    - Disk = 80 GB

You can also update the flavor to a one with a GPU, provided that you ask the CSC service desk [(8)](#used-material-8) to increase the cPouta project service quota with the following:

- Flavor = gpu.1.1gpu
    - CPU = 14
    - GPU = 1 NVIDIA Tesla P100
    - RAM = 117 GiB
    - Disk = 80 GB

Be aware that there is a limited number of GPUs on the cPouta platform, so you might not get access due to resource constraints. Fortunately, this will only prevent us from running GPU-based software on the cloud. Once you have decided the flavor you want to use and have created the VM, follow [(9)](#used-material-9) to connect to it with methods mentioned in [SSH chapter](./01_ssh.md).

If you ever have problems connecting to cPouta, it's likely due to security rules that prevent the client's IP address from connecting. The fix is to figure out the IP address and update the security rules. For example, this often happens when your local computer changes its IP address, which you can fix by checking your new IP address  [(10)](#used-material-10) and creating a new SSH rule for it.

## cPouta Docker

Please follow the provided materials to install Docker Engine with [(11)](#used-material-11) and remove sudo with [(12)](#used-material-12).

## cPouta volumes

The default storage for Docker is the 80 GB disk, which can become small if your use case includes LLMs. You might also want to save those files and, in the future, move the Docker files to other VMs. Both of these are solved with cPouta persistent volumes [(13)](#used-material-13). Use the provided materials to create a volume of at least 200 GB and attach it to your VM. We can configure it with the following steps:

0. Follow 'using attached volumes' instructions

1. Check the current root directory

```
docker info 
```

2. Create a folder in volume

```
cd /media/volume 
mkdir docker
```

3. Get its path

```
cd docker
pwd
```

4. Check docker daemon.json

```
cat /etc/docker/daemon.json
```

5. Shutdown Docker

```
sudo systemctl stop docker
sudo systemctl stop docker.socket
sudo systemctl stop containerd
```

6. Edit daemon.json to have data-root: '/media/volume/docker'

```
sudo nano /etc/docker/daemon.json
```

7. Confirm changes


```
cat /etc/docker/daemon.json
```

8. Move Docker data 

```
sudo rsync -axPS /var/lib/docker/ /media/volume/docker
```

9. Restart Docker


```
sudo systemctl start docker
```

10. Check Docker


```
docker info
```

11. Test Docker

```
docker run hello-world
```

12. Check the file system

```
df -h
```

Be aware that rebooting the VM [(14)](#used-material-14) will disconnect the volume from the VM, so you will need to reconnect it unless you modify the /etc/fstab configuration file. This is solved manually with:

```
sudo mount /dev/vdb /media/volume
sudo systemctl stop docker
sudo systemctl stop docker.socket
sudo systemctl stop containerd
sudo systemctl start docker
docker info
```

## cPouta GPUs

The cPouta Ubuntu images usually don’t include GPU drivers by default, so you might need to install NVIDIA drivers, CUDA, and the container toolkit. We used |[(15)](#used-material-15), [(16)](#used-material-16)| as the sources to get the following steps:

0. Update the environment. Press enter when you get a list

```
sudo apt update
sudo apt upgrade 
```

1. Check available GPUs

```
lspci | grep -i nvidia
```

2. Check that you already don't have drivers, CUDA, or container toolkit by confirming that these don't give versions

```
nvidia-smi
nvcc --version
dpkg -l | grep nvidia-container-toolkit
```

3. Get driver installers

```
sudo add-apt-repository ppa:graphics-drivers/ppa
sudo apt install ubuntu-drivers-common
ubuntu-drivers devices
```

4. Install a suitable driver


```
sudo apt install nvidia-driver-535
```

5. Reboot VM (Confirm that you are using the correct terminal)

```
Sudo reboot
```

6. Confirm drivers 

```
nvidia-smi
```

7. Download and install the CUDA repository pin

```
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
```

8. Download the CUDA repository Package

```
wget https://developer.download.nvidia.com/compute/cuda/12.2.0/local_installers/cuda-repo-ubuntu2204-12-2-local_12.2.0-535.54.03-1_amd64.deb
```

9. Install the CUDA repository package

```
sudo dpkg -i cuda-repo-ubuntu2204-12-2-local_12.2.0-535.54.03-1_amd64.deb
```

10. Install GPG key

```
sudo cp /var/cuda-repo-ubuntu2204-12-2-local/cuda-216F19BD-keyring.gpg /usr/share/keyrings/
```

11. Update package lists

```
sudo apt-get update
```

12. Install the CUDA toolkit

```
sudo apt-get -y install cuda
```

13. Set envs

```
echo 'export PATH=/usr/local/cuda-12.2/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.2/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

14. Verify installation

```
nvidia-smi
nvcc --version
```

15. Configure production repository

```
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
```

16. Update packages

```
sudo apt-get update
```

17. Install NVIDIA Container Toolkit

```
export NVIDIA_CONTAINER_TOOLKIT_VERSION=1.17.8-1
  sudo apt-get install -y \
      nvidia-container-toolkit=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
      nvidia-container-toolkit-base=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
      libnvidia-container-tools=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
      libnvidia-container1=${NVIDIA_CONTAINER_TOOLKIT_VERSION}
```

18. Configure Docker

```
sudo nvidia-ctk runtime configure --runtime=docker
```

19. Restart Docker daemon

```
sudo systemctl restart docker
```

20. Check daemon.json

```
cat /etc/docker/daemon.json
```

21. Configure kubernetes

```
sudo nvidia-ctk runtime configure --runtime=containerd
```

22. Restart containerd

```
sudo systemctl restart containerd
```

23. Check config.toml

```
cat /etc/containerd/config.toml
```

24. Check container toolkit

```
dpkg -l | grep nvidia-container-toolkit
```

25. Test Docker GPU

```
docker run --rm -it --gpus=all nvcr.io/nvidia/k8s/cuda-sample:nbody nbody -gpu -benchmark
```

26. Confirm the versions

```
nvidia-smi
nvcc --version
dpkg -l | grep nvidia-container-toolkit
```

It is recommended that you create a note about the driver, CUDA, and container toolkit versions that work. In our case they are:

- Driver = 535.288.01
- CUDA = release 12.2, V12.2.91
- Toolkit = 1.19.0-1

Be aware that any weird GPU problems are solved by either a CUDA [(15)](#used-material-15) or driver [(17)](#used-material-17) change. The old CUDA can be removed with:

```
sudo apt-get --purge remove '*cublas*' 'cuda*' 'nsight*' 
sudo apt-get autoremove
```

After that, return to step 7 to install the new CUDA. The old driver can be removed with:

```
sudo apt remove --purge '^nvidia-.*'
sudo apt remove --purge '^libnvidia-.*'
sudo apt autoremove
```

After that, do these before returning to step 4:

1. Restart containerd

```
sudo systemctl restart containerd
```

2. Check the available drivers

```
ubuntu-drivers devices
```

Please check the materials to double-check details. Now, your VM should be able to run Docker GPU containers, which we will later use to run LLMs.

---