import sys
import ray
import json
import time

from importlib.metadata import version

from actors.detector import Detector
from tasks.collector import data_collector

from icebreaker.storage.management import object_storage_interaction
from icebreaker.mlflow.setup import mlflow_setup_client

def das1_internal_data_analysis(
    process_parameters: any,
    storage_parameters: any,
    data_parameters: any
):
    try:  
        batch_input = data_parameters['input']
        given_actor_number = process_parameters['actor-number']
        
        file_batch_refs = []
        for file_batch in batch_input:
            file_batch_refs.append(ray.put(file_batch))
        # We assume that actor number isn't ridiculus
        actor_number = min(given_actor_number,len(batch_input))

        print('Creating ' + str(actor_number) + ' provider actors')
        actor_refs = []
        for i in range(0, actor_number):
            actor_refs.append(Detector.remote())

        print('Starting data collector tasks')
        task_1_refs = [] 
        worker_index = 1
        actor_index = 0
        for file_batch_ref in file_batch_refs:
            actor_ref = actor_refs[actor_index]
            task_1_refs.append(data_collector.remote(
                worker_index = worker_index,
                actor_index = actor_index + 1,
                actor_ref = actor_ref,
                data_parameters = data_parameters,
                file_tuples = file_batch_ref
            ))
            worker_index += 1
            actor_index = (actor_index + 1) % actor_number
        # We need to add the stats here into MLflow
        print('Waiting data collector tasks')
        collected_statistics = []
        while len(task_1_refs):
            done_task_1_refs, task_1_refs = ray.wait(task_1_refs)
            for output_ref in done_task_1_refs:
                collected_statistics.extend(ray.get(output_ref))
        
        mlflow_parameters = storage_parameters['mlflow-parameters']
        mlflow_client = mlflow_setup_client(
            mlflow_parameters = mlflow_parameters
        )
        
        experiment_id = mlflow_get_or_create_experiment(
            mlflow_client = mlflow_client,
            experiment_name = mlflow_parameters['experiment-name']
        )

        run_id = mlflow_start_run(
            mlflow_client = mlflow_client,
            experiment_id = experiment_id, 
            run_name = = mlflow_parameters['run-name'], 
            tags = mlflow_parameters['run-tags']
        )

        for statistics in collected_statistics:
            mlflow_log_metrics(
                mlflow_client = mlflow_client,
                run_id = run_id, 
                metrics = statistics, 
                step = 0
            ) 

        return True
    except Exception as e:
        print('das1 internal data analysis error', e)
        return False

if __name__ == "__main__":
    print('Starting Ray job')
    print('Python version is:' + str(sys.version))
    check_packages = [
        'ray',
        'python-swiftclient',
        'mlflow',
        'pandas',
        'pyarrow',
        'fasttext',
        'numpy',
        'mlflow'
    ]
    for pkg_name in check_packages:
        print(pkg_name,' version is ',version(pkg_name))
    
    print('Getting input')
    job_input = json.loads(sys.argv[1])
    process_parameters = job_input['process']
    storage_parameters = job_input['storage']
    data_parameters = job_input['data']

    print('Running DAS1 internal data analysis')
    task_status = das1_internal_data_analysis(
        process_parameters = process_parameters,
        storage_parameters = storage_parameters,
        data_parameters = data_parameters
    )

    print('Job success:' + str(task_status))
    print('Ray job Complete')