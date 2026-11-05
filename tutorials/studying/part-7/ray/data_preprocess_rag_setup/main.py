import sys
import ray
import json
import time as t

from importlib.metadata import version

from actors.generator import Generator
from tasks.setup import database_setup

from icebreaker.swift.setup import swift_setup_client
from icebreaker.pararellism.division import division_split_input
from icebreaker.qdrant.setup import qdrant_setup_client
from icebreaker.qdrant.use import qdrant_create_collection
from icebreaker.qdrant.utility import qdrant_hybrid_config
from icebreaker.misc.time import time_run_update

def internal_rag_setup(
    job_parameters: any
):
    try:  
        print('Parameters')
        swift_parameters = job_parameters['swift']
        input_storage_parameters = job_parameters['input-storage']
        rag_parameters = job_parameters['rag']
        config_parameters = job_parameters['config']
        dense_model_name = rag_parameters['dense-model-name']
        sparse_model_name = rag_parameters['sparse-model-name']
        process_parameters = job_parameters['process']
        device_mode = process_parameters['device-mode']
        qdrant_parameters = job_parameters['qdrant']
        qdrant_collection_name = rag_parameters['collection-name']
    
        work_qdrant_client = qdrant_setup_client(
            qdrant_parameters = qdrant_parameters
        )
        print('Qdrant client setup') 

        # This should be divided into batches based on worker number
        input_data = config_parameters['input']
        input_amount = len(input_data)
        
        if input_amount == 0:
            print("No input data provided.")
            return True

        print(f'Used dense model {dense_model_name}')
        print(f'Used sparse model {sparse_model_name}')

        print(f'Creating collection: {qdrant_collection_name}')
        status = qdrant_create_collection(
            qdrant_client = work_qdrant_client, 
            collection_name = qdrant_collection_name,
            configuration = qdrant_hybrid_config() 
        ) 

        worker_number = process_parameters['workers']
        print(f'Suggested amount of workers {worker_number}')
        suitable_worker_number = min(worker_number, input_amount)
        print(f'Selected amount of workers {suitable_worker_number}')

        worker_batches = division_split_input(
            job_input = input_data, 
            num_workers = suitable_worker_number
        )

        print(f'Batches created for {len(worker_batches)} workers')
        print(worker_batches)
        print('Putting data into refs')
        worker_batch_refs = []
        for worker_batch in worker_batches:
            worker_batch_refs.append(ray.put(worker_batch))

        amount_of_batches = len(worker_batches)
        actor_number = process_parameters['actors']
        print(f'Amount of batches {amount_of_batches}')
        print(f'Suggested amount of actors {actor_number}')
        suitable_actor_number = min(actor_number, amount_of_batches)
        print(f'Selected amount of actors {suitable_actor_number}')
        print(f'Using dense model: {dense_model_name}')
        print(f'Using sparse model: {sparse_model_name}')
        actor_refs = []
        for i in range(0, suitable_actor_number):
            actor_refs.append(Generator.remote(
                device_mode = device_mode,
                dense_model_name = dense_model_name,
                sparse_model_name = sparse_model_name
            ))

        print('Starting database setup tasks')
        task_1_refs = [] 
        worker_index = 1
        actor_index = 0
        for worker_batch_ref in worker_batch_refs:
            actor_ref = actor_refs[actor_index]
        
            task_1_refs.append(database_setup.remote( 
                worker_index = worker_index,
                actor_index = actor_index + 1,
                actor_ref = actor_ref,
                swift_parameters = swift_parameters,
                qdrant_parameters = qdrant_parameters,
                collection_name = qdrant_collection_name,
                input_storage_parameters = input_storage_parameters,
                config_parameters = config_parameters,
                task_batch = worker_batch_ref
            ))
            worker_index += 1
            actor_index = (actor_index + 1) % suitable_actor_number
        
        print('Waiting database setup tasks')
        waiting_outputs = []
        while len(task_1_refs):
            done_task_1_refs, task_1_refs = ray.wait(task_1_refs)
            for output_ref in done_task_1_refs:
                waiting_outputs.append(ray.get(output_ref))
        # This for some reason gives none
        print(waiting_outputs)
        return True
    except Exception as e:
        print(f'Internal rag setup error {e}')
        return False

if __name__ == "__main__":
    start_time = t.time()
    print('Starting Ray job')
    print('Python version is:' + str(sys.version))
    check_packages = [
        'ray',
        'python-swiftclient',
        'pandas',
        'pyarrow',
        'numpy',
        'torch',
        'torchvision',
        'transformers',
        'sentence-transformers',
        'huggingface-hub',
        'httpx',
        'brotli'
    ]

    for pkg_name in check_packages:
        try:
            print(f'{pkg_name} version is {version(pkg_name)}')
        except Exception as e:
            print(f'package not found error {e}')
    
    print('Getting input')
    job_parameters = json.loads(sys.argv[1])
    
    print('Running internal rag setup')
    task_status = internal_rag_setup(
        job_parameters = job_parameters
    )

    print('Job success:' + str(task_status))
    print('Ray job Complete')

    end_time = t.time()

    swift_parameters = job_parameters['swift']

    work_swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )

    time_storage_parameters = job_parameters['time-storage']
    time_storage_parameters['lock-location'] = job_parameters['process']['lock-location']
    time_object_name = time_storage_parameters['object-name']
    cluster_name = job_parameters['cluster']
    step_name = job_parameters['step']
    time_name = f'ray-internal-rag-setup-{cluster_name}-{step_name}'
    
    time_stored_1, time_index_1, time_name_1 = time_run_update(
        storage_client = work_swift_client,
        storage_parameters = time_storage_parameters,
        object_name = time_object_name,
        time_name = time_name,
        start_time = start_time,
        end_time = end_time,
        time_index = -1
    ) 
    
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)