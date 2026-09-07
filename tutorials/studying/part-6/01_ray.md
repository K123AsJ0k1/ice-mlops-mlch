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

In our case, we'll keep functions in the repository package for easier testing, which is why they usually don't exist in our Ray Scripts. To execute any code, we need to use either JobSubmissionClient or Ray client. The first one only requires a dashboard connection to run the following code:

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

## Local Compose Ray

## Cloud Kubernetes Ray

## HPC SLURM Ray

---