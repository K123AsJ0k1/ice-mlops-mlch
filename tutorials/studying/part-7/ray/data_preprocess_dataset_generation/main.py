import sys
import ray
import json
import time as t

from importlib.metadata import version

from collections import defaultdict

from actors.generator import Generator
from tasks.create import create_dataset

from icebreaker.swift.setup import swift_setup_client
from icebreaker.pararellism.division import division_split_input
from icebreaker.misc.time import time_run_update
from icebreaker.mlflow.setup import mlflow_setup_client
from icebreaker.mlflow.use import mlflow_get_or_create_experiment, mlflow_start_run, mlflow_add_logs, mlflow_end_run

def internal_dataset_creation(
    job_parameters: any
):
    try:  
        print('Parameters')
        swift_parameters = job_parameters['swift']
        mlflow_parameters = job_parameters['mlflow']
        input_storage_parameters = job_parameters['input-storage']
        config_parameters = job_parameters['config']
        model_parameters = job_parameters['model']
        process_parameters = job_parameters['process']
        server_name = process_parameters['server-name:']
          
        # This will be always single task and actor job
        '''
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
        '''
        # input gives a index range
        input_data = config_parameters['input']
        input_amount = len(input_data)

        if input_amount == 0:
            print("No input data provided.")
            return True

        worker_input_ref = ray.put(input_data)

        actor_ref = Generator.remote(
            server_name = server_name,
            model_parameters = model_parameters
        )

        print('Starting create dataset task')
        task_1_refs = [] 
        task_1_refs.append(create_dataset.remote( 
            worker_index = 1,
            actor_index = 1,
            actor_ref = actor_ref,
            swift_parameters = swift_parameters,
            input_storage_parameters = input_storage_parameters,
            index_range = worker_input_ref
        ))

        print('Waiting create dataset task')
        formatted_data = []
        while len(task_1_refs):
            done_task_1_refs, task_1_refs = ray.wait(task_1_refs)
            for output_ref in done_task_1_refs:
                formatted_data.append(ray.get(output_ref))
        '''
        print('Adding logs into MLflow') 
        for data in formatted_data:
            for dataset_name in data['metrics'].keys():
                parameters = data['parameters']
                metrics = data['metrics'][dataset_name]
                used_identity = dataset_name.split('extraction-data')[1][1:]
            
                mlflow_add_logs(
                    mlflow_client = mlflow_client,
                    run_id = run_id, 
                    parameters = parameters,
                    metrics = metrics,
                    metrics_prefix = used_identity,
                    metrics_step = 1,
                    table = {},
                    table_folder = '',
                    table_name = ''
                )
        
        print('Completing MLflow run')
        mlflow_end_run(
            mlflow_client = mlflow_client, 
            run_id = run_id, 
            status = 'FINISHED',
            end_time = None
        )
        '''
        
        return True
    except Exception as e:
        print(f'Internal dataset creation: {e}')
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
    task_status = internal_dataset_creation(
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
    '''
    time_stored_1, time_index_1, time_name_1 = time_run_update(
        storage_client = work_swift_client,
        storage_parameters = time_storage_parameters,
        object_name = time_object_name,
        time_name = time_name,
        start_time = start_time,
        end_time = end_time,
        time_index = -1
    ) 
    '''

    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)