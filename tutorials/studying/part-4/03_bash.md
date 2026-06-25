---
technologies: "Bash"
category: "Explanation and use of technology"
difficulty: "Intermediate"
---

# Bash

## Used material

1. <span id="used-material-1"></span> [The Bash Guide](https://guide.bash.academy/)

2. <span id="used-material-2"></span> [Kyoto University loses 77TB of supercomputer data after buggy update to HPE backup program](https://www.datacenterdynamics.com/en/news/kyoto-university-loses-77tb-of-supercomputer-data-after-buggy-update-to-hpe-backup-program/)

3. <span id="used-material-3"></span> [Software Update Deletes Everything Older than 10 Days](https://www.youtube.com/watch?v=Nkm8BuMc4sQ)

## Why use Bash?

Bash is widely used for the following reasons:

- Most common scripting language in development operations (mature)

- Easy use and simple syntax enable automating system management (abstracted)

- Widely supported on any Unix-based machine (interoperable)

These make Bash the default language for configuring environments and starting up software.  

## How to use Bash?

We will use Bash to create, modify, and execute small configuration or execution scripts. The details will be reduced to only relevant ones, so please check [(1)](#used-material-1) for more. When we create a Bash configuration script, we need to start with the following block:

```
#!/bin/bash

set -eo pipefail
```

This line is to reduce any shenanigans created by the fact that the default Bash ignores errors by forcing it to exit immediately (-e) and to say script failure if any part fails (-o pipefail). If you are interested in how bad Bash can fail, see [(2)](#used-material-2) and [(3)](#used-material-3). The simplest script we can have is the [hello world](./bash/hello_world.sh) file, which we can run in the following way:

```
cd bash
chmod +x hello_world.sh
./hello_world.sh
```

Usually, configuration scripts simply run long terminal commands, such as those shown in the [nvshare](./bash/oss_install_gpu_nvshare.sh) file. When we need to use multiple of these scripts and want the ability to select which to run, we can create conditional scripts, such as the [setup](./bash/oss_integration_setup.sh), that can be divided into the following steps:

1. Loads configuration

2. Gives you options

3. Checks available resources

4. Checks OS

5. Runs setup scripts

6. Applies YAMLs

7. Installs Helm if needed

8. Installs NVIDIA GPU operator and nvshare if needed

9. Installs Ray if needed

10. Runs tests

From these steps 2, 5, 7, 8, and 9, the configuration scripts actually run, while others gather variables or execute terminal commands. For this reason, if more configuration scripts are needed, they can simply be listed in step 2 and appended after step 9 for use during setup.

## Important parts of Bash

The most important parts to keep an eye on when trying to understand or develop Bash scripts are:

- Environment variables = The variables set on the host machine 

- Used variables = The variables set during execution

- Used commands = The manual commands you want to translate into automated execution

- Used scripts = The scripts that handle specific areas  

- Conditional states = The paths that execute different scripts 

---