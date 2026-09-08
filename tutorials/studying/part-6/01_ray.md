---
technologies: "Ray"
category: "Choice and use of technology"
difficulty: "Intermediate"
---

# Ray

## Used material

1. <span id="used-material-1"></span> [Ray pip package](https://pypi.org/project/ray/)

2. <span id="used-material-2"></span> [Ray docs](https://docs.ray.io/en/latest/)

3. <span id="used-material-3"></span> [Ray: The Complete Guide from Beginner to Professional](https://medium.com/@sjbpr1/ray-the-complete-guide-from-beginner-to-professional-74160d98749b)

4. <span id="used-material-4"></span> [Ray dockerhub](https://hub.docker.com/r/rayproject/ray)

## Why use Ray?

Ray is the most common unified scaling framework for Pythonic Web, Big Data, and AI for the following reasons:

- Provides a unified execution engine used by the largest tech companies in the world that is fault-tolerant and can scale up to any use case (mature)

- Easy-to-use Python primitives for abstracted distributed programming that enable heterogeneous resource scheduling and creation of hardware-agnostic codebases (abstracted)

- Supports a wide range of high-level libraries that integrate with other packages, can be used in both local, cloud, and HPC environments, and enables shared memory for optimizing distributed processing.

These features make Ray the default computing framework for local-cloud-HPC integration, enabling us to incrementally create parallelized code that we can easily move between environments and use to distribute tasks on the most suitable hardware.

## How to use Ray?

In our use case, we will use Ray to handle data analysis, data preprocessing, model serving, and model evaluation, with occasional automated interactions, which you can get an in-depth look at using |[(1)](#used-material-1), [(2)](#used-material-2), [(3)](#used-material-3)|. The most important terms related to using Ray are:

- Job scripts
- JobSubmissionClient 
- Ray client
- Parameters
- Runtime
- Batch jobs
- Requirements
- Tasks
- Actors
- Resource specifications
- Serve
- Objects
- Pipeline
- Parallelism

Ray job scripts are self-contained folders with the requirements, main, and functions needed to complete the desired tasks. An example folder structure is:

- job_script
    - main.py
    - requirements.txt
    - tasks
    - actors
    - functions

In our case, we'll keep functions in the repository package for easier testing, which is why they usually don't exist in our Ray job scripts. To execute any code, we need to use either JobSubmissionClient or Ray client. The first one only requires a dashboard connection to run the following code:

```
from ray.job_submission import JobSubmissionClient

ray_job_client = JobSubmissionClient(
    address = 'http://127.0.0.1:8265'
)
```

The second one requires more configuration because Ray is sensitive to package and Python versions. We will not use this option to keep it simple across clusters. When you want to execute a ready Ray script, you need to submit it in the following way:

```
import json
execution_command = "python main.py"
execution_command = execution_command + " '" + json.dumps(ray_parameters) + "'"
job_id = ray_client.submit_job(
    entrypoint = "python main.py",
    runtime_env = ray_runtime
)
```

In this code, the ray_parameters contains a nested dictionary with values that support or modify script behavior. The main.py reads them as follows:

```
if __name__ == "__main__":
    import json
    job_parameters = json.loads(sys.argv[1])
```

In the same code, ray_runtime contains a nested dictionary that includes at least working_dir, with an absolute path to a Ray script folder, and pip, with either a list of packages or a requirements path inside the Ray script folder that lists the used Python packages. You can also add arguments such as env_vars to provide environment variables. An example runtime can be:

```
{
    'working_dir': '/home/$USER/main_staging/ice-mlops-mlch/applications/pipelines/rag-coding-assistant/model_evalution_server',
    'pip': '/home/$USER/main_staging/ice-mlops-mlch/applications/pipelines/rag-coding-assistant/model_evalution_server/requirements.txt',
    'env_vars': {
        'TOKEN': 'test'
    }
}
```

When you submit a Ray script with suitable parameters to run as a batch job, it first installs the necessary packages listed in requirements.txt. This setup can fail for myriad reasons, with version dependencies or missing packages being common causes. Be aware, however, that the Ray cluster caches packages to reduce reinstalling, which is why you need to change requirements.txt each time you think there is a problem with a package. A solution for this minimal change is to have the following text at the start of the requirements.txt:


```
# cache-bust: v1
```

This lets you increment the number to force the cluster to reinstall all packages, which is handy if you just fixed a custom package. Once the package installation succeeds, execution begins with main.py, where we use a main function to set up the expected tasks and actors with suitable resource configurations. Ray tasks are distributed asynchronous function calls executed across the cluster that return object references called futures. Ray actors are distributed asynchronous classes that hold mutable state and handle tasks sequentially. Both are processed within available resources based on resource specifications. Here are examples of tasks and actors:

```
import ray
@ray.remote(
    num_cpus = 1,
    memory = 0.2 * 1024 * 1024 * 1024
) 
def task(input: any):
    pass
 
@ray.remote(
    num_cpus = 1,
    num_gpus = 1,
    memory = 0.2 * 1024 * 1024 * 1024
) 
class actor:
    def __init__(self,parameters: any):
        pass

    def actor_task(self, input: any):
        pass
```

The actor can be extened to be a serve instance that can be interacted using REST in the following way:

```
import time as t
from ray import serve
from fastapi import FastAPI, Request

app = FastAPI()

@serve.deployment(
    num_replicas = 1,
    ray_actor_options = {
        "num_cpus": 1, 
        "num_gpus": 1
    } 
)
@serve.ingress(app)
class serve:
    def __init__(self, parameters: any):
        pass
    
    @app.post("/generate")
    async def actor_task(self, input: any):
        pass

if __name__ == "__main__":
    job_parameters = json.loads(sys.argv[1])
    serve.start(
        http_options = {
            'host': job_parameters['host'],
            'port': job_parameters['port']
        }
    ) 

    serve.run(
        serve.bind(
            parameters = job_parameters
        ), 
        name = 'serve', 
        route_prefix='/'
    )  
    # Enables deleting this instances
    # serve.delete(name = 'serve') 
    # Deletes all serve instances
    # serve.shutdown()  
```

Serve instances enable fast prototyping of ideas, but batch jobs should use only tasks and actors. The main function of a batch job is to create the number of task and actor instances based on the provided parameters by first defining the input object to be shared between tasks. Objects are variables stored in the Ray cluster object store. The utilization consists of the following functions:

```
import ray
variable = 1
object_ref = ray.put(variable)
object_value = ray.get(object_ref)
```

Be aware that passed references to tasks and actors resolve themselves, removing the need to use ray.get(), unless you have a list of references. With these concepts, we can create pipeline parallelism using the following pattern:

```
def main_function(job_parameters: any)
    worker_number = job_parameters['workers']
    actor_number = job_parameters['actors']
    actor_parameters = job_parameters['actor-parameters']
    input_data = job_parameters['input']
    
    worker_batches = division_split_input(
        job_input = input_data, 
        num_workers = worker_number
    )

    worker_batch_refs = []
    for worker_batch in worker_batches :
        worker_batch_refs.append(ray.put(worker_batch))

    actor_refs = []
    for i in range(0, suitable_actor_number):
        actor_refs.append(actor.remote(
            parameters = actor_parameters
        ))

    task_1_refs = [] 
    worker_index = 1
    actor_index = 0
    for worker_batch_ref in worker_batch_refs:
        actor_ref = actor_refs[actor_index]
        task_1_refs.append(task.remote(
            worker_index = worker_index,
            actor_index = actor_index + 1,
            actor_ref = actor_ref,
            input = worker_batch_ref
        ))
        worker_index += 1
        actor_index = (actor_index + 1) % suitable_actor_number

    collected_statistics = {} 
    while len(task_1_refs):
        done_task_1_refs, task_1_refs = ray.wait(task_1_refs)
        for output_ref in done_task_1_refs:
            collected_statistics.update(ray.get(output_ref))

    return collected_statistics
```

This pattern can be repeated sequentially to have a longer pipeline in the Ray script. Still, since we have access to object storage and various computing infrastructures, it is much better to have a maximum of 1-2 parallel steps per Ray script to keep them short, enable easier distribution of tasks, and make the workflow using these Ray scripts more tolerant of failure. We will go more in depth later on how to create Ray-based workflows.

## Local and cloud Compose Ray

Assuming you have installed Docker on your local computer or cloud virtual machine as described in the [Docker chapter](../part-1/07_docker.md), we can setup a local and cloud Ray cluster with the example [compose YAML](./deployments/local-cloud-compose-ray-cluster.yaml). This can be done in the following steps:

1. Go to the folder

```
cd ice-mlops-mlch/tutorials/studying/part-6/deployments
```

2. Edit the CPU, RAM, and GPU amounts to fit the host.

```
ray-head:
    deploy:
        resources:
            reservations: 
                devices: # remove if you don't have NVIDIA GPU
                - driver: nvidia
                    count: 1
                    capabilities: [gpu]
                limits:
                    cpus: '30' # reduce to maximum-2CPUs aka (32-2) = 30
                    memory: '15g' # reduce to around half of maximum-1GB = (32/2-1) = 15GB   
```

3. Confirm if you are going to use CPU or GPU docker image [(4)](#used-material-4).

```
(ray-head/ray-worker):
    image: rayproject/ray:2.49.2-py312-(cu128/cpu)
```

4. Run the YAML with compose.

```
docker compose -f local-cloud-compose-ray-cluster.yaml up
```

5. If there are no errors, you should be able to check the dashboard at http://localhost:8265. If you plan to use Ray Serve, set the address to 0.0.0.0 and the port to 8350 to enable interactions at http://localhost:8350.

6. To shut down the cluster, run CTRL + C. You can also stop it with

```
docker compose -f local-cloud-compose-ray-cluster.yaml stop
```

With this, you have a local or cloud cluster that you can distribute tasks to utilize available resources. However, be aware that the biggest challenge with local clusters is resource constraints, which are further reduced by the operating system and any other background tasks. 

The main resource you will always lack is RAM, which is why the shown compose YAML puts most of the resources into the ray-head. You must also account for limited RAM when planning workflow batch jobs to prevent them from failing due to OOM errors.

For these reasons, unless you have proper local servers, the local side will be used to enable incremental development of your workflow and Ray scripts. It also provides a workflow speedup depending on input distribution, which we cover in more detail later.

## Cloud Kubernetes Ray

Assuming you have checked the KubeRay mentioned in the [Helm chapter](../part-4/07_helm.md), we can set it up using the example [YAML configuration](./deployments/cloud-kubernetes-ray-cluster.yaml). This can be done in the following way:

1. Confirm whether you will use a CPU or GPU image [(4)](#used-material-4). The latter requires that you have completed the setup described in the [KinD chapter](../part-4/05_kind.md).

2. Edit the CPU, RAM, and GPU amounts to fit your cloud virtual machine.

```
head:
  resources:
    limits:
      cpu: "4" # reduce to half of available cpus-1CPUs aka (10/2-1) = 4
      memory: "52G" # reduce to around half of maximum-1GB aka (106/2-1) = 52 GB
      nvshare.com/gpu: "1" # Use this to share a single GPU with nvshare
    requests:
      cpu: "4" # reduce to maximum-2CPUs aka (32-2) = 30
      memory: "52G"

worker:
  resources:
    limits:
      cpu: "4" # reduce to half of available cpus-1CPUs aka (10/2-1) = 4
      memory: "52G" # reduce to around half of maximum-1GB aka (106/2-1) = 52 GB
      nvshare.com/gpu: "1" # Use this to share a single GPU with nvshare
    requests:
      cpu: "4" # reduce to maximum-2CPUs aka (32-2) = 30
      memory: "52G" # reduce to around half of maximum-1GB aka (106/2-1) = 52 GB
```

3. Assuming you have a running KubeRay operator and not Ray Cluster, use the following command to create a new cluster:

```
cd ice-mlops-mlch/tutorials/studying/part-6/deployments
helm install raycluster kuberay/ray-cluster --version 1.0.0 -f cloud-kubernetes-ray-cluster.yaml
```

4. Confirm that the Ray cluster pod status is running.

```
kubectl get pods 

NAME                                     READY   STATUS      RESTARTS       AGE
kuberay-operator-9986f78b7-599nf         1/1     Running     12 (28h ago)   10d
nvshare-tf-matmul-1                      0/1     Completed   0              31d
nvshare-tf-matmul-2                      0/1     Completed   0              31d
raycluster-kuberay-head-jjx4s            1/1     Running     0              10d
raycluster-kuberay-worker-worker-8kd9v   1/1     Running     0              10d
```

5. Assuming you have setup KinD networking with the [Istio chapter](../part-4/11_istio.md), you should be able to local forward to the virtual machine and check the dashboard using http://ray.cloud.dash-1.oss:7001. When running serve, set the address to 0.0.0.0 and the port to 8000 to use http://ray.cloud.serve-1.oss:7001 for interactions.

With this, you have a Kubernetes cloud cluster that can easily interact with other services running in the Kind platform. This enables faster Ray script prototyping than local and cloud Compose clusters. Still, it can be limited by the resources available to the Kind platform and by how many services request those same resources.

Resource challenges generally depend on how easy and cheap it is to add more resources with your cloud vendor. For example, for CSC for academic institutions, you only need to send an email with a good reason to the service desk to get more resources, and it's free for those institutions. A way to consider the resources a KinD platform requires is to use the following command:

```
kubectl describe nodes
Allocated resources:
  (Total limits may be over 100 percent, i.e., overcommitted.)
  Resource           Requests            Limits
  --------           --------            ------
  cpu                13135m (93%)        35200m (251%)
  memory             113800869120 (92%)  126371972Ki (104%)
  ephemeral-storage  0 (0%)              0 (0%)
  hugepages-1Gi      0 (0%)              0 (0%)
  hugepages-2Mi      0 (0%)              0 (0%)
  nvidia.com/gpu     1                   1
  nvshare.com/gpu    2                   2

```

Here, Kubernetes allocates resources to services using the requests and limits provided by those services. Be aware that requests are the minimum amount of resources, while limits are the maximum amount of resources for a specific pod. 

As long as the resource configuration isn't so large that the pod stays in pending status, Kubernetes will run it. This is called guaranteed scheduling, which aims to ensure that no node is ever overcommitted beyond its capacity at deployment. 

---