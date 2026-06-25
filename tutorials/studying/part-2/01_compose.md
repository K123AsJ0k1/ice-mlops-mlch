---
technologies: "Docker Compose"
category: "Explanation and use of technology"
difficulty: "Easy"
---

# Docker Compose
 
## Used material

1. <span id="used-material-1"></span> [Docker Compose docs](https://docs.docker.com/compose/)

2. <span id="used-material-2"></span> [Docker Compose Quickstart](https://docs.docker.com/compose/gettingstarted)

3. <span id="used-material-3"></span> [Run Redis Open Source on Docker](https://redis.io/docs/latest/operate/oss_and_stack/install/install-stack/docker/)

## Why use Docker Compose?
 
Docker Compose is widely used for the following reasons:

- One of the most common orchestration tools (mature)

- Easy way to setup full software stacks (abstracted)

- Usable in any place that supports Docker (interoperable)

These make Docker Compose the default container orchestrator for local environments, enabling us to develop, test, and run containers before moving them to other environments.

## How to use Docker Compose?

Assuming your Docker Desktop is setup [(1)](#used-material-1), you only need to write a YAML file to run Docker containers [(2)](#used-material-2). For example, we can run a Redis container by using the [redis](./redis.yaml) file in the following way:

```
docker compose -f redis.yaml up
```

You can stop it with:

```
CTRL + C
```

In the given YAML file the most important things are:

- Service-name = tutorial-redis
    - Used for networking inside docker
- Image-name = redis:8.2.1
    - The image used in running the container
- Ports = 127.0.0.1:6379:6379
    - Used for networking outside docker

These are common problem points when creating interconnected software stacks, since they address how containers connect to each other, what software runs in each container, and how to interact with the container. For more complex problems check Docker docs [(1)](#used-material-1) or the documentation of the software you are using such as Redis [(3)](#used-material-3).

---