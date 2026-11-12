import sys
import ray
import json
import time as t

from importlib.metadata import version

from actors.judge import Judge
from tasks.evalute import evaluate_dataset

from icebreaker.swift.setup import swift_setup_client
from icebreaker.misc.time import time_run_update
from icebreaker.mlflow.setup import mlflow_setup_client
from icebreaker.mlflow.use import mlflow_get_or_create_experiment, mlflow_start_run, mlflow_add_logs, mlflow_end_run

def answer_judge_process(
    job_parameters: any
):
    try:  
        print('Parameters')
        swift_parameters = job_parameters['swift']
        mlflow_parameters = job_parameters['mlflow']
        input_storage_parameters = job_parameters['input-storage']
        solution_storage_parameters = job_parameters['solution-storage']
        output_storage_parameters = job_parameters['output-storage']
        config_parameters = job_parameters['config']
        judge_parameters = job_parameters['judge']
        judge_prompts = config_parameters['judge-prompts']
        process_parameters = job_parameters['process']
        server_name = process_parameters['server-name']  
        # This will be always single task and actor job
        
        print('Setup MLflow')  
        mlflow_client = mlflow_setup_client(
            mlflow_parameters = mlflow_parameters
        )
        
        experiment_id = mlflow_get_or_create_experiment(
            mlflow_client = mlflow_client,
            name = mlflow_parameters['experiment-name']
        )
        '''
        run_id = mlflow_start_run(
            mlflow_client = mlflow_client,
            experiment_id = experiment_id, 
            run_name = mlflow_parameters['run-name'], 
            tags = mlflow_parameters['run-tags']
        )
        print('MLflow setup') 
        '''
        
        # input gives a index range
        input_data = config_parameters['input'][0]
        input_amount = len(input_data)
        print(input_data)
        if input_amount == 0:
            print("No input data provided.")
            return True

        worker_input_ref = ray.put(input_data)

        judge_ref = Judge.remote(
            server_name = server_name,
            model_parameters = judge_parameters
        )

        print('Starting evaluate dataset task')
        task_1_refs = [] 
        task_1_refs.append(evaluate_dataset.remote( 
            worker_index = 1,
            actor_index = 1,
            judge_ref = judge_ref,
            judge_parameters = judge_parameters,
            swift_parameters = swift_parameters,
            mlflow_parameters = mlflow_parameters,
            experiment_id = experiment_id,
            input_storage_parameters = input_storage_parameters,
            solution_storage_parameters = solution_storage_parameters,
            output_storage_parameters = output_storage_parameters,
            worker_input = worker_input_ref,
            judge_prompts = judge_prompts
        ))

        print('Waiting answer dataset')
        formatted_data = []
        while len(task_1_refs):
            done_task_1_refs, task_1_refs = ray.wait(task_1_refs)
            for output_ref in done_task_1_refs:
                formatted_data.append(ray.get(output_ref))
        '''
        for data in formatted_data:
            parameters = data['parameters']
            metrics = data['metrics']
            used_identity = data['identity']

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
        print(f'Answer judge process: {e}')
        return False

if __name__ == "__main__":
    start_time = t.time()
    print('Starting Ray job')
    print('Python version is:' + str(sys.version))
    check_packages = [
        'ray',
        'python-swiftclient',
        'llama-cpp-python',
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
    
    print('Running answer judge process')
    task_status = answer_judge_process(
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
    time_name = f'ray-answer-judge-process-{cluster_name}-{step_name}'
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