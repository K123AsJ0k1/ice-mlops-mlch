---
technologies: "Environment constraints"
category: "Explanation and use of concept"
difficulty: "Intermediate"
---

# Environment constraints

## Used material

1. <span id="used-material-1"></span> [A Design Framework for Cloud-HPC Integration in MLOps](https://dl.acm.org/doi/10.1145/3672608.3707866) 

## What are environment constraints?

As we summarize in the [ICE chapter](../part-1/02_ice.md), when we integrate various environments into an MLOps platform, each environment has its own benefits and limitations that must be considered during implementation. We can describe these trade-offs as development constraints for local, cloud, storage and HPC in the areas of security, resources, and experience in the following way:

- Local:
    - Security: 
        - Controller private access (CPA): Expects all utilization of local computing to be under host control
    - Resources:
        - Available minimum borrowing (AMB): Allows software to run within the shared, constrained local resources
    - Experience:
        - Flexible software utilization (FSU): Enables local infrastructure to host almost any kind of software
        
- Cloud:
    - Security:
        - Secured minimum access (SMA): Allows users and applications to utilize virtual machine (VM) instances via a secure communication protocol
    - Resources:
        - Requested minimum borrowing (RMB): Enables users to create VM instances with set resources within the limits set by the user's budgets and ecosystem resources
    - Experience: 
        - Stateless microservice utilization (SMU): Expects users to divide applications into small disposable components for better tolerance and scalability

- Storage:
    - Security:
        - Controlled authenticated access (CAA): Enables users and applications to interact with storage using provided methods
    - Resources:
        - Controlled consumption borrowing (CCB): Makes users spend as they store within the limits of the user's budget and ecosystem resources
    - Experience:
        - Global store utilization (GSU): Enables applications to get and store data with various clients and users to access the store via dashboards
- HPC:
    - Security: 
        - Secured individual access (SIA): Enforces the utilization of the HPC platform by individual users and their tools via a secure communication protocol
    - Resources:
        - Resource reservation borrowing (RRB): Expects the batch jobs submitted by the user to have enough time and resources for successful completion
    - Experience:
        - Optimized cluster utilization (OCU): Requires minimized impact and efficient utilization of allocated resources by the users and tools interacting with the HPC cluster

These constraints enable us, during the design and implementation of the local-cloud-HPC integrated MLOps platform, to consider the development requirements of each infrastructure. This makes it easier to select and design suitable software to enable unified pipelines based on maturity, interoperability, and abstraction. 

## How to use environment constraints?

We will use environment constraints to evaluate the demonstrated local-cloud-HPC MLOps platform. As shown in [(1)](#used-material-1), the evaluation will check each constraint and the platform's ability to meet the development requirements. Ideally, the platform would have a solution for each constraint, but some are hard to achieve completely, such as SMU, because OSS is not completely disposable. We will cover this in more detail later.

---