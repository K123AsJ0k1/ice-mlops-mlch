import sys
import ray
import json
import time as t
import pandas as pd

from importlib.metadata import version

from actors.detector import Detector
from tasks.filter import data_filter
from collections import defaultdict

from icebreaker.swift.setup import swift_setup_client
from icebreaker.pararellism.division import division_split_input
from icebreaker.misc.time import time_run_update

from icebreaker.objects.use import objects_store_data
from icebreaker.data.use import data_list_objects

def evalution_dataset_creation(
    job_parameters: any
):
    try:  
        print('Parameters')
        swift_parameters = job_parameters['swift']
        data_storage_parameters = job_parameters['data-storage']
        result_storage_parameters = job_parameters['result-storage']
        config_parameters = job_parameters['config']
        model_parameters = job_parameters['model']
        process_parameters = job_parameters['process']
        dataset_parameters = config_parameters['dataset-parameters']
        target_rows = dataset_parameters['target-rows']
         
        print('Dividing work')
        input_data = config_parameters['input']
        input_amount = len(input_data)
        worker_number = process_parameters['workers']
        
        print(f"Total target N rows: {target_rows}")
        print(f'Amount of inputs {input_amount}')
        target_per_dataset = max(1, target_rows // input_amount)
        remainder = target_rows - (target_per_dataset * input_amount)
        print(f'Target rows per dataset {target_per_dataset}')
        print(f'Reminder {remainder}')

        dataset_targets = {}
        for idx, item in enumerate(input_data):
            path = item[0]
            extra = 1 if idx < remainder else 0
            dataset_targets[path] = target_per_dataset + extra
        
        print(f'Suggested amount of workers {worker_number}')
        suitable_worker_number = min(process_parameters['workers'], input_amount)
         
        print(f'Selected amount of workers {suitable_worker_number}')
        worker_batches = division_split_input(
            job_input = input_data, 
            num_workers = suitable_worker_number
        )

        worker_dataset_targets = []
        for batch in worker_batches:
            profile = {}
            for item in batch:
                profile[path] = dataset_targets[path]
            worker_dataset_targets.append(profile)

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
            actor_refs.append(Detector.remote(
                swift_parameters = swift_parameters,
                model_parameters = model_parameters
            ))

        print('Starting data collector tasks')
        task_1_refs = [] 
        worker_index = 1
        actor_index = 0
        for worker_batch_ref in worker_batch_refs:
            actor_ref = actor_refs[actor_index]
            worker_targets = worker_dataset_targets[worker_index - 1]

            task_1_refs.append(data_filter.remote( 
                worker_index = worker_index,
                actor_index = actor_index + 1,
                actor_ref = actor_ref,
                swift_parameters = swift_parameters,
                data_storage_parameters = data_storage_parameters,
                config_parameters = config_parameters,
                target_rows = target_rows,
                task_batch = worker_batch_ref,
                worker_targets = worker_targets
            ))
            worker_index += 1
            actor_index = (actor_index + 1) % actor_number
         
        print('Waiting data collector tasks')
        all_unified_rows = []
        while len(task_1_refs):
            done_task_1_refs, task_1_refs = ray.wait(task_1_refs)
            for output_ref in done_task_1_refs:
                all_unified_rows.extend(ray.get(output_ref))
        print(all_unified_rows)
        final_dataset_df = pd.DataFrame(
            all_unified_rows, 
            columns = [
            'question',
            'answer',
            'language',
            'format'
        ])
        print(f"Total collected rows: {len(final_dataset_df)}")

        if target_rows < len(final_dataset_df):
            final_dataset_df = final_dataset_df.sample(n = target_rows, random_state = 42).reset_index(drop = True)
            print(f"Normalized dataset down to accurate target row amount N: {len(final_dataset_df)}")

        work_swift_client = swift_setup_client(
            swift_parameters = swift_parameters
        )
    
        dataset_prefix = result_storage_parameters['object-name']
        object_list = data_list_objects(
            storage_client = work_swift_client,
            storage_parameters = result_storage_parameters,
            object_prefix = dataset_prefix 
        )

        next_index = len(object_list) + 1
        cluster_name = job_parameters['cluster']
        step_name = job_parameters['step']
        dataset_object_name = f'{dataset_prefix}-{next_index}-{cluster_name}-{step_name}' 
        
        stored_status = objects_store_data(
            swift_client = work_swift_client,
            storage_parameters = {
                'bucket-target': result_storage_parameters['bucket-target'],
                'bucket-prefix': result_storage_parameters['bucket-prefix'],
                'bucket-user': result_storage_parameters['bucket-user'],
                'object-name': 'data',
                'object-serialization': 'parquet',
                'path-replacers': {
                    'name': dataset_object_name 
                },
                'path-names': [],
                'debug-prints': True,
                'lock-parameters': {},
                'lock-location': None,
                'overwrite': True
            },
            object_data = final_dataset_df,
            object_metadata = {}
        )
        return True
    except Exception as e:
        print('evalution dataset creation', e)
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
        'fasttext',
        'magika',
        'numpy'
    ]
    for pkg_name in check_packages:
        try:
            print(f'{pkg_name} version is {version(pkg_name)}')
        except Exception as e:
            print(f'package not found error {e}')
    
    print('Getting input')
    job_parameters = json.loads(sys.argv[1])
    
    print('Running external data analysis')
    task_status = evalution_dataset_creation(
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
    time_name = f'ray-evalution-dataset-creation-{cluster_name}-{step_name}'
    
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