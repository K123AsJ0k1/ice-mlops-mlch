import ray
import time as t
import pickle
from icebreaker.swift.setup import swift_setup_client
from icebreaker.storage.management import object_storage_interaction
from icebreaker.pyarrow.use import pyarrow_deserialize_dataframe

@ray.remote(
    num_cpus = 1,
    memory = 0.2 * 1024 * 1024 * 1024
) 
def database_setup(
    worker_index: int,
    actor_index: int,
    actor_ref: any,
    swift_parameters: any,
    data_storage_parameters: any,
    config_parameters: any,
    task_batch: any,
    target_profile: dict
) -> any: 
    start_time = t.time()
    print(f'Task {worker_index}, Actor {actor_index}')
    
    print('Setting up swift client')
    work_swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )
    print('Swift client setup') 

    suitable_dataframe_rows = []
    for batch_data in task_batch:
        object_path = batch_data[0]

        max_target_for_this_path = target_profile.get(object_path, 0)

        if max_target_for_this_path <= 0:
            continue
        
        stored_dataset = object_storage_interaction(
            storage_client = work_swift_client,
            parameters = {
                'mode': 'get',
                'bucket-target': data_storage_parameters['bucket-target'],
                'bucket-prefix': data_storage_parameters['bucket-prefix'],
                'bucket-user': data_storage_parameters['bucket-user'],
                'debug-prints': True,
                'object-name': 'root',
                'path-replacers': {
                    'name': object_path
                },
                'path-names': [],
                'overwrite': True,
                'lock-parameters': {},
                'lock-location': ''
            },
            object_data = None,
            object_metadata = None
        )  
        pandas_df = pyarrow_deserialize_dataframe(serialized_dataframe = stored_dataset[0])
        
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return suitable_dataframe_rows