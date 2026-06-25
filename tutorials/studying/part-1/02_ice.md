---
technologies: "Integrated computing environments"
category: "Explanation and use of concept"
difficulty: "Intermediate"
---
 
# Integrated computing environments

## Used material

1. <span id="used-material-1"></span> [A Design Framework for Cloud-HPC Integration in MLOps](https://dl.acm.org/doi/10.1145/3672608.3707866) 

## Why use integrated computing environments?

The integration of computing environments (ICE) aims to enable the use of tools and resources from separate computing dimensions and distributed platforms to create and maintain specific computational use cases. In the case of MLOps, using ICE as a design framework can enable the development of tools for:

- Dimensional scaling = Unifying dimensions such as Internet of Things, edge, local, storage, cloud, high-performance, and quantum to use their unique tools and resources in ML development 

- Distributed scaling = Unifying platforms provided by ecosystems such as CSC, AWS, GCP, and Azure to access their specific tools and resources in ML development.

The ideal outcome of these efforts would be a MLOps platform that enables scalable, agnostic, and reliable ML workflows that can run ML pipelines regardless of hardware, software, or vendor.

## How to use integrated computing environments?

The integration of computing environments, such as cloud-HPC integration, uses the following to enable interactions between separated systems:

- Platform access = Access to the CSC platform is provided through a MyCSC account, which uses SSH keys (secure cryptographic keys that allow safe remote login).

- Interaction interface = Interaction occurs via the Linux terminal (a text-based interface to control operating systems).

- Global storage = CSC Allas object storage (a cloud-based system for saving files and data used jointly by multiple systems).

- Interaction automation = Apache Airflow to run automation Python code (an open-source software tool to program and monitor complex data workflows).

- Cooperative communication = Communication between systems is achieved by storing and retrieving objects in the CSC Allas storage.

- Action monitoring = Monitoring actions is done through logs (records of events or operations) created by Airflow, Submitter, and Forwarder programs.

The utilization of the interactive system depends on the tools enabled by the environment:

- Local environment = Owned computers can run almost anything within available resources.

- Cloud environment = Virtual machines can run anything within the limits of vendor resources, terms of service, and available budget.

- Storage environment = Object storage can store anything within the limits of vendor resources, terms of service, and available budget.

- High-performance computing environment = Supercomputers enable program execution in vendor-approved ways in a shared computing cluster.

These result in the following environmental trade-offs:

- Local has easy usability, but limited resources (you have as many resources as you are willing to spend on hardware and maintenance)

- Cloud has flexible resources, but limited scalability (you have as many resources as the vendor and your budget allows)

- Storage has dedicated storage, but utilization dependencies (you can only store in predefined ways that the use environment must enable)

- HPC has scalable computing, but limited usability (there is curated access, and you can only do things within the rules the vendor sets)

For these reasons, we need to select and design software for the integration based on how it enables achieving the following attributes [(1)](#used-material-1):

- Maturity = How old, used, and supported is the tool? 

- Abstraction = How many irrelevant and relevant details does the tool filter out to be user-friendly?

- Interoperability = How hardware, operating system, and programming language agnostic is the tool? 

---