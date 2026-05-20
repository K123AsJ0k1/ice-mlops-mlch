import sys
import ray
import json
import time

from importlib.metadata import version

from actors.detector import Detector
from tasks.collector import data_collector

from icebreaker.storage.management import object_storage_interaction

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
        
        # Load these into MLflow
        return True
    except Exception as e:
        print('das1 internal data analysis error', e)
        return False

if __name__ == "__main__":
    print('Starting Ray job')
    print('Python version is:' + str(sys.version))
    print('Ray version is:' + version('ray'))
    
    print('Getting input')
    job_input = json.loads(sys.argv[1])
    process_parameters = job_input['process']
    storage_parameters = job_input['storage']
    data_parameters = job_input['data']

    print('Running parallel processing')
    task_status = das1_internal_data_analysis(
        process_parameters = process_parameters,
        storage_parameters = storage_parameters,
        data_parameters = data_parameters
    )

    print('Job success:' + str(task_status))
    print('Ray job Complete')
