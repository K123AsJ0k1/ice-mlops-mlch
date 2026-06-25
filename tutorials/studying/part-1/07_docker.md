---
technologies: "Docker"
category: "Explanation and use of technology"
difficulty: "Intermediate"
---

# Docker
 
## Used material

1. <span id="used-material-1"></span> [Docker Engine docs](https://docs.docker.com/engine/)

2. <span id="used-material-2"></span> [Docker Desktop docs](https://docs.docker.com/desktop/)

3. <span id="used-material-3"></span> [Docker Engine Linux post-installation steps](https://docs.docker.com/engine/install/linux-postinstall/)

4. <span id="used-material-4"></span> [Docker Desktop Windows GPU](https://docs.docker.com/desktop/features/gpu/)

## Why use Docker?
 
Docker is widely used for the following reasons:

- One of the most common containerization tools (mature)

- Easy way to run Python software anywhere (abstracted)

- Widely supported in local and cloud platforms with similar options in HPC platforms (interoperable)

These make Docker the default containerization tool for running software in the MLOps context, because it enables users to focus on application coding and networking issues rather than spending effort figuring out the unique configurations of different machines.

## How to use Docker?

You need to either install Docker Engine [(1)](#used-material-1) or Docker Desktop [(2)](#used-material-2) on your machine. The practical way is to use Docker Engine on cloud machines and Docker Desktop on local machines. Be aware that on Linux, the Docker engine requires additional configuration to remove the need for sudo in Docker commands [(3)](#used-material-3), and on Windows, Docker Desktop automatically configures available GPUs for use in containers [(4)](#used-material-4).  

---