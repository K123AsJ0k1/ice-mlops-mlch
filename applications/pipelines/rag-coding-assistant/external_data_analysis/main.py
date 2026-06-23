import sys
import ray
import json
import time as t

from importlib.metadata import version

from actors.detector import Detector
from tasks.collector import data_collector

from icebreaker.swift.setup import swift_setup_client
from icebreaker.mlflow.setup import mlflow_setup_client
from icebreaker.mlflow.use import mlflow_get_or_create_experiment, mlflow_start_run, mlflow_log_metrics, mlflow_change_run_status
from icebreaker.pararellism.division import division_split_input
from icebreaker.misc.dict import flatten_nested_dict
from icebreaker.misc.time import time_run_update

def external_data_analysis(
    job_parameters: any
):
    try:  
        print('Parameters')
        swift_parameters = job_parameters['swift']
        mlflow_parameters = job_parameters['mlflow']
        data_storage_parameters = job_parameters['data-storage']
        config_parameters = job_parameters['config']
        model_parameters = job_parameters['model']
        process_parameters = job_parameters['process']

        print('Setup MLflow')
        mlflow_client = mlflow_setup_client(
            mlflow_parameters = mlflow_parameters
        )
        
        experiment_id = mlflow_get_or_create_experiment(
            mlflow_client = mlflow_client,
            name = mlflow_parameters['experiment-name']
        )

        run_id = mlflow_start_run(
            mlflow_client = mlflow_client,
            experiment_id = experiment_id, 
            run_name = mlflow_parameters['run-name'], 
            tags = mlflow_parameters['run-tags']
        )
        print('MLflow setup')
        # This should be divided into batches based on worker number
        print('Dividing work')
        input_data = config_parameters['input']
        input_amount = len(input_data)
        worker_number = process_parameters['workers']
        print(f'Amount of inputs {input_amount}')
        print(f'Suggested amount of workers {worker_number}')
        suitable_worker_number = min(process_parameters['workers'], input_amount)
        print(f'Selected amount of workers {suitable_worker_number}')
        worker_batches = division_split_input(
            job_input = input_data, 
            num_workers = suitable_worker_number
        )
        print('Batches created for ', len(worker_batches), ' workers')
        print(worker_batches)
        print('Putting data into refs')
        worker_batch_refs = []
        for worker_batch in worker_batches:
            worker_batch_refs.append(ray.put(worker_batch))
        # We assume that actor number isn't ridiculus
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
            task_1_refs.append(data_collector.remote(
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
        collected_statistics = {} 
        while len(task_1_refs):
            done_task_1_refs, task_1_refs = ray.wait(task_1_refs)
            for output_ref in done_task_1_refs:
                collected_statistics.update(ray.get(output_ref))
        # remember that metrics only takes integers or floats
        print('Flattening output')
        flattened_statistics = flatten_nested_dict(
            target_dict = collected_statistics,
            parent_key = '',
            seperator = '-'
        )

        # Maybe also store the metrics in allas for later use

        print('Logging metrics into MLflow')
        mlflow_log_metrics(
            mlflow_client = mlflow_client,
            run_id = run_id, 
            metrics = flattened_statistics, 
            step = 0
        ) 
        print('Completing MLflow run')
        mlflow_change_run_status(
            mlflow_client = mlflow_client, 
            run_id = run_id, 
            status = 'FINISHED'
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
    ]
    # Some cases require fasttext wheel
    for pkg_name in check_packages:
        try:
            print(f'{pkg_name} version is {version(pkg_name)}')
        except Exception as e:
            print(f'package not found error {e}')
    
    print('Getting input')
    job_parameters = json.loads(sys.argv[1])
    
    print('Running external data analysis')
    task_status = external_data_analysis(
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
    time_name = f'ray-external-data-analysis-{cluster_name}-{step_name}'
    
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