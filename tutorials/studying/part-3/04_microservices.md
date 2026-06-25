---
technologies: "Microservices"
category: "Explanation and use of technology"
difficulty: "Easy"
---

# Microservices 
 
## Used material

1. <span id="used-material-1"></span> [What is monolithic architecture](https://www.ibm.com/think/topics/monolithic-architecture)

2.  <span id="used-material-2"></span> [The Ultimate Guide to Docker](https://medium.com/@belemgnegreetienne/the-ultimate-guide-to-docker-benefits-architecture-and-practical-steps-02d0f02e7eee)

3. <span id="used-material-3"></span> [Should I use separate Docker containers for my web app?](https://stackoverflow.com/questions/30534939/should-i-use-separate-docker-containers-for-my-web-app)

4. <span id="used-material-4"></span> [Docker Microservice Architecture](https://www.devzero.io/blog/docker-microservices)

5. <span id="used-material-5"></span> [Microservices with FastAPI and Docker](https://medium.com/@shrinit.poojary12/microservices-with-fastapi-and-docker-a-step-by-step-guide-63edaadb65b2)

6. <span id="used-material-6"></span> [A Guide to Using Kubernetes for Microservices](https://www.vcluster.com/blog/a-guide-to-using-kubernetes-for-microservices)

7. <span id="used-material-7"></span> [Design science](https://en.wikipedia.org/wiki/Design_science_(methodology))

8. <span id="used-material-8"></span> [A Design Framework for Cloud-HPC Integration in MLOps](https://dl.acm.org/doi/10.1145/3672608.3707866)


## Why use microservices?

Microservice architectures [(1)](#used-material-1) are a software development style that splits code responsibility into smaller components. In the case of machine learning operations (MLOps), microservices architectures provide the following:

- Modularity = The requirements of a specific component can be handled by self-developed, open-source, or proprietary software

- Independence = Each component has its own responsibility and interacts only via interfaces.

- Scalability = Modularity lets us meet demands by adding components

- Automation = The modularity and independence of each component enable us to set up automated development workflows, such as continuous integration/continuous delivery, to reduce effort 

- Interfaced = The modularity and independence enable us to focus on creating interfaces for software interactions 

- Abstraction = The modularity, independence, and interfaces enable us to design systems based only on requirements, which means we can start development from the angle we want

These enable us to use microservice architectures to create mature, abstracted, and interoperable systems that run in Docker |[(2)](#used-material-2), [(3)](#used-material-3), [(4)](#used-material-4), [(5)](#used-material-5)| and Kubernetes [(6)](#used-material-6),  using interfaces to interact with separate systems. 

## How to use microservices?

The previous chapters have shown the necessary pieces for building a microservice architecture to enable automation of interactions between separated systems that consist of the following components:

- Principles = [Machine learning operations](../part-1/01_mlops.md)

- Design = [Integrating computing environments](../part-1/02_ice.md)

- Language = [Python](../part-1/03_python.md)

- Development = [Jupyter Lab](../part-1/04_jupyterlab.md)

- Interfaces = [Pydantic](../part-1/05_pydantic.ipynb)

- Configuration = [YAML](../part-1/06_yaml.ipynb)

- Containers = [Docker](../part-1/07_docker.md)

- Orchestration = [Docker Compose](../part-2/01_compose.md)

- Cache = [Redis](../part-2/02_redis.ipynb)

- Frontend = [FastAPI](../part-2/03_fastapi.ipynb)

- Backend = [Celery](./01_celery.ipynb)

- Monitoring = [Flower](./02_flower.ipynb)

- Scheduling = [Beat](./03_beat.md)

This is due to the use and synergies with Design Science Research Methodology [(7)](#used-material-7), which was used to design and implement cloud-HPC integration [(8)](#used-material-8). Microservice architectures removed the need to nail down exactly what software to use by simply allowing the use of pipeline functions that generalize to common MLOps workflows. This enabled the creation of theoretical pipelines for searching for software that fit the functions, and for creating software that filled the gaps between them. The resulting minimum viable product was then evaluated against objectives, constraints, and metrics to inform the next development iteration of the architecture and implementation. 

The iterative development of integrated computing environments for MLOps use cases can easily become overwhelming due to architectural complexity, harder testing, security constraints, differences across systems, and the wide range of technologies required to build the necessary microservice applications. Fortunately, the selection and design of software based on maturity, abstraction, and interoperability alleviate this by reducing the development effort required in each iteration, enabling the production of increasingly better solutions for integrating separated computing environments. 

---