---
technologies: "Allas"
category: "Choice and use of technology"
difficulty: "Easy"
---

# Allas

## Used material

1. <span id="used-material-1"></span> [Allas](https://research.csc.fi/service/allas-data-storage-service-for-research-projects/)

2. <span id="used-material-2"></span> [The Allas object storage](https://docs.csc.fi/data/Allas/)

3. <span id="used-material-3"></span> [Accessing Allas](https://docs.csc.fi/data/Allas/accessing_allas/)

4. <span id="used-material-4"></span> [CAP theorem](https://en.wikipedia.org/wiki/CAP_theorem)

## Why use Allas? 

The Allas OpenStack S3-based storage platform provided by the Center of Scientific Computing (CSC) is the easiest and fastest way to access storage services for education and research in Finland [(1)](#used-material-1). The S3 infrastructure storage is widely used for the following reasons:

- One of the most common infrastructure architectures for scalable, durable, and cost-efficient data storage for different use cases (mature)

- Enables varied management methods via clients, CLIs, and UIs (abstracted)

- Utilization is widely supported by different hardware, operating systems, and programming languages (interoperable)

These enable us to use the CSC-run Allas to create data containers (buckets) to store varied types of data (objects) that we can easily retrieve anywhere, provided we know their identities (key), which we can use to centralize data management into an easily accessible and fault-tolerant system that offers synergistic benefits for other services provided by CSC.

## How to use Allas?

Assuming that you have setup a MyCSC account and a CSC project mentioned in the [cPouta chapter](../part-4/02_cpouta.md), we can gain access to Allas by enabling the service [(2)](#used-material-2) in MyCSC. We will again only provide relevant details, so you should check the details from [(2)](#used-material-2) as necessary. When Allas is enabled, check [(3)](#used-material-3) for different ways to access it. For our use case, the access methods are the UI and Python clients, with the latter elaborated later. The dashboard can be accessed either via the [cPouta dashboard](https://pouta.csc.fi/) by clicking the project object store and containers or via the [Allas dashboard](https://allas.csc.fi/). Both are valid methods; the former may be more convenient, so the choice is left to you.

## Storage management

Object storage platforms, such as Allas, provide guaranteed availability and partition tolerance, with some providing strong consistency based on the CAP theorem [(4)](#used-material-4). CAP theorem states that distributed data stores can provide at most 2 guarantees out of 3, which are:

- Consistency = All data reads receive the most recent write or an error

- Availability = Every request receives a non-error response without guaranteeing the most recent write

- Partition tolerance = The system continues to operate regardless of an arbitrary number of messages being dropped by the network between nodes.

The selections lead to the following database systems:

- CP system = Networking break makes the system refuse to respond to requests to ensure data integrity (for example, Redis)

- AP system = Networking break doesn't affect nodes, but they can't sync latest updates, until network is fixed to enable eventual consistency (for example, Allas)

- CA system = Assumes network reliability or there is a single node (for example, PostgreSQL)

The implications of Allas being an AP system with eventual consistency require us to plan our storage management. The read and write operations in our use case involve many concurrent reads and writes, with many write-once, read-many operations. This plan needs to specify how we use the buckets, how we create object paths and how we handle objects. 

Our use case expects users to be either individuals or small teams of 3-6 who use the same MyCSC project and even the same cloud cPouta VMs to enable MLOps. The application runs on their local computers and uses SSH connections to run commands and manage files in the HPC platform. Communication and storage between local, cloud, and HPC are provided by object storage Allas, where local and cloud applications store concurrent read-write communication objects and application-specific write-once artifact objects that are read by different local, cloud, and HPC applications. Thus, we can formulate the following storage managmenet plan for Allas:

- Buckets = Containers that separate purpose, application, and user data
    - All buckets are named (identity)-(name)
        - Identity = mlch
        - Name = for-air, sub-air, pipe, and exp
    - We add (user) to separate multiple application instances
        - User = user-example-com
- Path = Keys that separate the purpose, application, and use of data
    - All buckets have their own folder-like structure
        - mlch-for-air 
            - ARTIFACTS
                - TASKS
                - TIMES
            - DEPLOYMENTS
                - FORWARD
        - mlch-sub-air-user-example-com 
            - MANAGEMENT
            - ARTIFACTS
                - TASKS
                - TIMES
        - mlch-pipe-user-example-com 
            - ARTIFACTS
                - SACCT
            - CODE
                - RAY
                - SLURM
            - LOGS
            - TIMES
        - mlch-exp-user-example-com 
            - DATA
                - SOURCE
                - EVALUATION
                - VALIDATION
            - ARTIFACTS
                - PROMPTS
                - METRICS
                - TIMES
- Objects = Data that contains a variety of modalities separated by type
    - All objects should have metadata, and most should be serialized
        - Metadata
            - Version = Incremented number that starts from 1
        - Serialization
            - Pickle = Used for Python data structures
            - Parquet = Used for tabular data
    - If serialization isn't possible, either use none or other suitable formats
    - Communication objects need to reduce the possibility of reading and writing stale data 
        - Applications and humans can read the object at any time
        - Different applications should be ordered into a step-by-step write workflow
        - Automation needs to handle stale data by assuming a step-by-step workflow
        - Concurrent writes need to be handled with Redis using first-come, first-served 
        - The structure of the object needs to have areas of responsibility for parallelism
        - We will assume that automation interacts with objects, not humans
        - Templates must be used to ensure a consistent object structure during creation
        - All object interactions must be done through frontend APIs 
        - Automation workflows must always get the object before modifying it to prevent stale data
    - Artifact objects need to be consistently named and minimize data use
        - Applications and humans can read the object at any time
        - Applications can store as many relevant objects as they can within reason and data staleness
        - In larger scales, the objects need to be divided into batches 

This storage management plan uses storage isolation with standardized paths and objects to ensure that the distributed system only accesses the area of responsibility it is allowed to. It keeps read-write access to the object user, with parallelism and concurrency handled by distributed locking, and other applications can only read until it's their turn in the data manipulation workflow. These together reduce the risk of automation receiving stale data while providing an easy-to-understand storage structure for transferring data between systems.

---