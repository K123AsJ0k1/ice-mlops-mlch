import sys
import ray
import json
import time as t

from importlib.metadata import version

from actors.generator import Generator
from tasks.setup import database_points

from icebreaker.swift.setup import swift_setup_client
from icebreaker.pararellism.division import division_split_input
from icebreaker.misc.time import time_run_update
from icebreaker.qdrant.setup import qdrant_setup_client
from icebreaker.qdrant.use import qdrant_upload_points, qdrant_create_collection, qdrant_baai_hybrid_config

def rag_database_setup(
    job_parameters: any
):
    try:  
        print('Parameters')
        swift_parameters = job_parameters['swift']
        data_storage_parameters = job_parameters['data-storage']
        config_parameters = job_parameters['config']
        model_parameters = job_parameters['model']
        process_parameters = job_parameters['process']

        qdrant_parameters = job_parameters['qdrant-parameters']
        qdrant_collection = job_parameters['collection-name']

        work_qdrant_client = qdrant_setup_client(
            qdrant_parameters = qdrant_parameters
        )
        print('Qdrant client setup') 

        # This should be divided into batches based on worker number
        input_data = config_parameters['input']
        input_amount = len(input_data)
        if 0 < input_amount:
            print(f'Creating collection: {qdrant_collection}')
            status = qdrant_create_collection(
                qdrant_client = work_qdrant_client, 
                collection_name = qdrant_collection,
                configuration = qdrant_baai_hybrid_config() 
            )

            print('Dividing work')
            worker_number = process_parameters['workers']
            
            print(f'Suggested amount of workers {worker_number}')
            suitable_worker_number = min(process_parameters['workers'], input_amount)
            # Here the processing considers going through the given object paths to get N row dataset
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
            suitable_actor_number = min(actor_number,amount_of_batches)
            print(f'Selected amount of actors {suitable_actor_number}')
            actor_refs = []
            for i in range(0, suitable_actor_number):
                actor_refs.append(Generator.remote(
                    swift_parameters = swift_parameters,
                    model_parameters = model_parameters
                ))

            print('Starting data collector tasks')
            task_1_refs = [] 
            worker_index = 1
            actor_index = 0
            for worker_batch_ref in worker_batch_refs:
                actor_ref = actor_refs[actor_index]
            
                task_1_refs.append(database_points.remote( 
                    worker_index = worker_index,
                    actor_index = actor_index + 1,
                    actor_ref = actor_ref,
                    swift_parameters = swift_parameters,
                    data_storage_parameters = data_storage_parameters,
                    config_parameters = config_parameters,
                    task_batch = worker_batch_ref
                ))
                worker_index += 1
                actor_index = (actor_index + 1) % actor_number
            
            print('Waiting data collector tasks')
            all_hybrid_points = []
            while len(task_1_refs):
                done_task_1_refs, task_1_refs = ray.wait(task_1_refs)
                for output_ref in done_task_1_refs:
                    all_hybrid_points.extend(ray.get(output_ref))

            print('Uploading points')
            status = qdrant_upload_points(
                qdrant_client = work_qdrant_client, 
                collection_name = qdrant_collection,
                points = all_hybrid_points
            ) 
        
        return True
    except Exception as e:
        print('external data analysis error', e)
        return False

if __name__ == "__main__":
    start_time = t.time()
    print('Starting Ray job')
    print('Python version is:' + str(sys.version))
    check_packages = [
        'ray',
        'python-swiftclient',
        'mlflow',
        'pandas',
        'pyarrow',
        'fasttext',
        'magika',
        'numpy',
        'mlflow'
    ]
    for pkg_name in check_packages:
        print(pkg_name,' version is ',version(pkg_name))
    
    print('Getting input')
    job_parameters = json.loads(sys.argv[1])
    
    print('Running external data analysis')
    task_status = rag_database_setup(
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
    time_object_name = time_storage_parameters['object-name']

    cluster_name = job_parameters['cluster']
    step_name = job_parameters['step']
    time_name = f'ray-rag-database-setup-{cluster_name}-{step_name}'
    
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