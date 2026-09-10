---
technologies: "Parallelism"
category: "Explanation and use of concept"
difficulty: "Intermediate"
---

# Parallelism

## Used material

1. <span id="used-material-1"></span> [Efficient LLMs Training and Inference: An Introduction](https://www.researchgate.net/publication/385916997_Efficient_LLMs_Training_and_Inference_An_Introduction)

## Why use Parallelism?

MLOps and LLMOps use parallelism to split tasks across multiple CPU and GPU units, improving resource use and execution speed, using the following strategies  [(1)](#used-material-1):

- Data Parallelism = Splitting input data across multiple nodes running the same model, with each processing a different subset
    - Pros: 
        - Simplicity = Easy to implement by duplicating a model and splitting data
        - Scalability = Efficient scaling as the number of nodes increases
    - Cons:
        - Memory redundancy = Each node stores the same model, leading to memory inefficiencies as size increases
        - Communication overhead = Model gradients must be synchronized across nodes, leading to communication overhead as the number of nodes increases

- Tensor Parallelism = Splitting a model's tensors across multiple GPUs, with each GPU computing different parts of the model's layers
    - Pros:
        - Memory efficiency = Splitting tensors reduces memory requirements per GPU, which allows processing larger models
        - Scalability of large layers = Larger model layers can be distributed across multiple GPUs to decrease the computation burden
    - Cons:
        - Complexity = Implementing tensor splitting and its communication across GPUs adds complexity
        - Communication overhead = Frequent exchange of results between GPUs can create overhead and reduce gained speedup

- Pipeline Parallelism = Splitting a model into different stages, with each stage using a different GPU, to enable simultaneous processing of multiple batches
    - Pros: 
        - Memory distribution = Distributing the model reduces the memory burden of an individual GPU
        - Improved utilization = Overlapping computation of different batches can lead to better GPU utilization and reduced idle time
    - Cons:
        - Pipeline bubbles = The pipeline must be filled, leading to a delay before full utilization, aka pipeline bubble 
        - Complexity in implementation = The model must be carefully divided into stages alongside its inter-stage communication

The differences between them are the following:

- Data parallelism vs. tensor parallelism
    - Memory usage = Tensor parallelism reduces memory usage across GPUs, while data parallelism has redundancy due to storing the model on all GPUs
    - Communication = Data parallelism primarily uses gradient synchronization, while tensor parallelism uses frequent communication of intermediate results

- Data parallelism vs. pipeline parallelism:
    - Applicability = Data parallelism is simpler and used when the model fits into a single GPU, while pipeline parallelism is complex and used for large models that don't fit into a single GPU 
    - Efficiency = Data parallelism has communication bottlenecks with large numbers of GPUs, and pipeline parallelism needs to handle pipeline bubbles and use complex scheduling

- Tensor parallelism vs. pipeline parallelism:
    - Layer granularity = Tensor parallelism handles individual model layers across GPUs, while pipeline parallelism uses coarser granularity to split the model into stages
    - Communication overhead = Tensor parallelism has more intra-layer communication overhead, while pipeline parallelism uses communication mostly between stages

These 3 strategies are widely used to optimize LLM training: data parallelism handles large datasets and scales across GPUs, tensor parallelism splits large layers between GPUs, and pipeline parallelism divides the model into stages to distribute computational load and memory requirements. We will use similar strategies to speed up use-case workflow pipelines and use resources efficiently. 

## How to use Parallelism?

For our use case, we will use pipelined execution and data partitioning for data analysis and preprocessing, reserving the terms data parallelism, tensor parallelism, and pipeline parallelism for LLM inference. 

Pipelined execution will use suitable dictionary schemas, Python functions, and orchestration tools so users can create a pipeline dictionary with all necessary input information and steps to run Ray scripts. 

Data partitioning will use object storage paths, Python functions, and cluster-specific Ray script configurations to first divide the given object paths between clusters, then divide those object paths between Ray tasks, and finally divide the data to be processed by Ray actors. 

We will cover data partitioning here with pipelined execution coming later. We have already covered partitioning data for Ray tasks in the [Ray chapter](./01_ray.md), which is why we will go over dividing the data for clusters and actors. The cluster division uses load balanced round robin to divide a list Allas objects between available clusters during each workflow step with the following code:

```
from ..ray.use import ray_get_clients
from ..data.use import data_list_objects
from ..pararellism.division import (
    division_formatted_clusters, 
    division_cluster_weights,
    division_load_balanced_cluster_round_robin
)

cluster_yamls = integration['cluster-yamls']
cluster_priority = integration['cluster-priority']
hardware_influence = integration['hardware-influence']
workflow_steps = integration['workflow-steps']
resource_weights = integration['resource-weights']
data_storage = storage['data-storage']
min_initial_inputs = integration['min-initial-inputs']
min_batch_size = integration['min-batch-size']
step_processing_parameters = processing['step-1']
step_cluster_parameters = step_processing_parameters['cluster']

cluster_clients = ray_get_clients(
    configured_clusters = cluster_yamls,
    cluster_parameters = step_cluster_parameters,
    cluster_filter = []
)

formatted_clusters = division_formatted_clusters(
    ray_clusters = cluster_clients
) 

cluster_weights = division_cluster_weights(
    resource_weights = resource_weights,
    formatted_clusters = formatted_clusters,
    cluster_priority_percentages = cluster_priority,
    hardware_influence = hardware_influence
)

object_prefix = processing[step_key]['general']['data-storage']['object-prefix']
dataset_tuple_list = data_list_objects(
    storage_client = storage_client,
    storage_parameters = data_storage,
    object_prefix = object_prefix
)

cluster_division = division_load_balanced_cluster_round_robin(
    target_list = dataset_tuple_list,
    cluster_weights = cluster_weights,
    min_initial_inputs = min_initial_inputs,
    min_batch_size = min_batch_size
)

for cluster_name, cluster_input in cluster_division.items():
    print(f'{cluster_name} given batch input size {str(len(cluster_input))}')
    if not cluster_name in cluster_tracks:
        cluster_tracks[cluster_name] = []
    
    cluster_tracks[cluster_name].append({
        'cluster_step': step_key,
        'cluster_name': cluster_name,
        'cluster_input': cluster_input
    })

track_inputs = []
for used_name, used_input in cluster_tracks.items():
    track_inputs.append(used_input)
```

This code uses the provided example [parameters](./parameters/local-cloud-parameters.yaml) to calculate cluster weights, determine the object path prefix to list objects from Allas, divide the list between clusters, and process the division into a suitable list. 

More specifically, the load-balanced round-robin uses the provided hardware details (CPUs, RAM, and GPUs), along with the set resource weights and cluster priority percentages, to divide objects by size across clusters. For example, here is a example division of 126 objects with parameters

- resource-weights:
    - cpu: 0.95
    - ram: 0.05
- cluster-priority:
    - cloud-vm1: 0.04
    - cloud-vm2: 0.29
    - local-lt1: 0.02
    - local-lt2: 0.25
    - local-lt3: 0.4
- hardware-influence: 0.0
- min-initial-inputs: 1
- min-batch-size: 1

gives the following result:

```
cloud-vm1 given batch input size 5
cloud-vm2 given batch input size 36
local-lt1 given batch input size 3
local-lt2 given batch input size 31
local-lt3 given batch input size 51
```

With this, we simplified data partitioning by giving objects suitable names, enabling path prefixes to select the desired list of object paths to divide. After the Ray script divides these paths among available Ray tasks, each task must split them into batches to use available actors efficiently within resource constraints. 

The main goal is to divide the object data into batch sizes that the most constrained infrastructure can process, ensuring actor RAM or VRAM use does not cause OOM errors. Here is an example pattern for actor batching:

```
import ray

from icebreaker.swift.setup import swift_setup_client
from icebreaker.objects.use import objects_get_data
from icebreaker.qdrant.setup import qdrant_setup_client
from icebreaker.qdrant.use import qdrant_create_point, qdrant_upload_points
from icebreaker.embeddings.utility import embeddings_generate_uuid

@ray.remote(
    num_cpus = 1,
    memory = 0.2 * 1024 * 1024 * 1024
) 
def database_setup(
    worker_index: int,
    actor_index: int,
    actor_ref: any,
    swift_parameters: any,
    qdrant_parameters: any,
    collection_name: str,
    data_storage_parameters: any,
    config_parameters: any,
    process_parameters: any,
    task_batch: any
) -> any:
    work_swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )
    
    work_qdrant_client = qdrant_setup_client(
        qdrant_parameters = qdrant_parameters
    )

    text_column = config_parameters['text-column']
    process_batch_size = process_parameters['vector-batch-size']
    generator_actor_refs = []
    dataset_records_map = {}
    for data_index, batch_data in enumerate(task_batch):
        object_path = batch_data[0]
        
        data_object = objects_get_data(
            swift_client = work_swift_client,
            storage_parameters = {
                'bucket-target': data_storage_parameters['bucket-target'],
                'bucket-prefix': data_storage_parameters['bucket-prefix'],
                'bucket-user': data_storage_parameters['bucket-user'],
                'object-name': 'root',
                'object-serialization': data_storage_parameters['object-serialization'],
                'path-replacers': {
                    'name': object_path
                },
                'path-names': [],
                'debug-prints': True,
                'lock-parameters': {},
                'lock-location': None,
                'overwrite': True
            },
            dict_format = False
        )  
        
        pandas_df = data_object[0]
        df_records = pandas_df.to_dict('records')
        dataset_records_map[data_index] = df_records

        total_rows = len(pandas_df)
        calclated_chunk = int(total_rows * 0.05)
        chunk_size = max(1, calclated_chunk)
        for i in range(0, total_rows, chunk_size):
            df_chunk = pandas_df.iloc[i : i + chunk_size]
            text_chunk = df_chunk[text_column].tolist()
            chunk_row_indices = list(range(i, i + len(df_chunk)))
            
            text_input_ref = ray.put(text_chunk)
            generator_actor_refs.append(actor_ref.batch_generate_vectors.remote(
                worker_index = worker_index, 
                actor_index = actor_index, 
                data_index = data_index,
                batch_index = i,
                object_path = object_path, 
                text_input_batch = text_input_ref,
                batch_size = process_batch_size,
                row_indices = chunk_row_indices
            ))

    hybrid_points = []
    while len(generator_actor_refs) > 0:
        done_refs, generator_actor_refs = ray.wait(generator_actor_refs)
        for output_ref in done_refs: 
            batch = ray.get(output_ref)
            
            batch_dataset_index = batch['data_idx']
            batch_object_path = batch['object_path']
            dense_vectors = batch['dense']
            sparse_vectors = batch['sparse']
            row_indices = batch['row_indices']

            dataset_name = batch_object_path.split('/')[-1].split('.')[0]
            source_records = dataset_records_map[batch_dataset_index]

            for idx_in_chunk, actual_row_idx in enumerate(row_indices):
                d_vec = dense_vectors[idx_in_chunk] if dense_vectors is not None else None
                s_vec = sparse_vectors[idx_in_chunk] if sparse_vectors is not None else None
                
                dataset_row = source_records[actual_row_idx]

                point_uuid = embeddings_generate_uuid(
                    id = dataset_name,
                    index = actual_row_idx
                )

                created_point = qdrant_create_point(
                    point_uuid = point_uuid,
                    point_dense_vector = {"dense": d_vec} if d_vec else None,
                    point_sparse_vector = {"sparse": s_vec} if s_vec else None,
                    point_payload = dataset_row
                )
                hybrid_points.append(created_point)
        
    status = qdrant_upload_points(
        qdrant_client = work_qdrant_client, 
        collection_name = collection_name,
        points = hybrid_points
    ) 
    return True
```

This code sets up a database by iterating through the given object paths, sending them to actors in 5% batches, waiting for the actors to complete the batches, and processing the information to store in a database. This pattern is very similar to the previously shown task pattern, except that each task assigns its batches to a single actor. 

It's sensible to have more tasks than actors because actors use persistent resources to load heavy models and handle heavy calculations. In contrast, tasks aim to use these resources efficiently by sending a balanced number of batches. Both help ensure the Ray script runs within the cluster resources, since this lets us adjust resource requirements. We will cover more details later.

---