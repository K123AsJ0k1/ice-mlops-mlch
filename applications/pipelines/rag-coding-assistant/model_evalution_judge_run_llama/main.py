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