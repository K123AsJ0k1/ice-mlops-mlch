import sys
import ray
import json
import time

from importlib.metadata import version

from actors.detector import Detector
from tasks.collector import data_collector

from icebreaker.mlflow.setup import mlflow_setup_client
from icebreaker.mlflow.use import mlflow_get_or_create_experiment, mlflow_start_run, mlflow_log_metrics, mlflow_change_run_status
from icebreaker.pararellism.division import division_split_input
from icebreaker.misc.dict import flatten_nested_dict

def das1_internal_data_analysis(
    job_parameters: any
):
    try:  
        print('Parameters')
        storage_parameters = job_parameters['storage']
        data_parameters = job_parameters['data']
        process_parameters = job_parameters['process']
        model_parameters = job_parameters['model']

        mlflow_parameters = storage_parameters['mlflow-parameters']
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
        input_data = data_parameters['input']
        given_worker_number = process_parameters['worker-number']

        worker_batches = division_split_input(
            job_input = input_data, 
            num_workers = given_worker_number
        )
        print('Batch amount', len(worker_batches))
        print(worker_batches)
        print('Putting data into refs')
        worker_batch_refs = []
        for worker_batch in worker_batches:
            worker_batch_refs.append(ray.put(worker_batch))
        # We assume that actor number isn't ridiculus
        given_actor_number = process_parameters['actor-number']
        actor_number = min(given_actor_number,len(worker_batches))
        
        swift_parameters = storage_parameters['swift-parameters']
        #model_parameters = storage_parameters['model-parameters']
        print('Creating ' + str(actor_number) + ' provider actors')
        actor_refs = []
        for i in range(0, actor_number):
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
                storage_parameters = storage_parameters,
                data_parameters = data_parameters,
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
        print('Logging metrics into MLflow')
        flattened_statistics = flatten_nested_dict(
            target_dict = collected_statistics,
            parent_key = '',
            seperator = '-'
        )
        #print(collected_statistics)
        #for key_name, key_metrics in collected_statistics.items():
        #    print('Adding ', key_name, ' stats')
        #    print(key_metrics)
        print(flattened_statistics)
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
    job_parameters = json.loads(sys.argv[1])
    #process_parameters = job_input['process']
    #storage_parameters = job_input['storage']
    #data_parameters = job_input['data']

    print('Running DAS1 internal data analysis')
    task_status = das1_internal_data_analysis(
        job_parameters = job_parameters
    )

    print('Job success:' + str(task_status))
    print('Ray job Complete')