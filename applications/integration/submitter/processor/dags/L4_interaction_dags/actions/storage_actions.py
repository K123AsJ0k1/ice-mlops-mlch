# Check imports and inputs
def storage_action_orchestration_interaction(
    swift_client: any,
    bucket_parameters: any,
    storage_parameters: any
) -> bool:
    try:
        import pickle
        from icebreaker.models.orchestration import Orchestration
        from icebreaker.storage.management import object_storage_interaction
        from icebreaker.misc.dict import update_nested_dict
        from icebreaker.misc.time import time_orch_update
        from icebreaker.interactions.caching import caching_save_dict
    except ImportError as e:
        raise ImportError("interaction-dags/sub_func/storage failed to import", e)

    store_action = storage_parameters['store-action']
    bucket_target = bucket_parameters['target']
    bucket_prefix = bucket_parameters['prefix']
    bucket_user = bucket_parameters['user']
    debug_prints = storage_parameters['debug-prints']

    object_key = '1' 
    stored_data = {}
    stored_metadata = {'version': 1}
    if store_action == 'create':
        object_input = storage_parameters['object-input']
        if 0 < len(object_input):
            # Checking is done here for cleaner logs
            validation_model = Orchestration.model_validate(object_input)
            stored_data = object_input
            
            object_key = object_storage_interaction(
                storage_client = swift_client,
                lock_parameters = storage_parameters['lock'],
                lock_location = storage_parameters['airflow-lock-location'],
                parameters = {
                    'mode': 'index',
                    'bucket-target': bucket_target,
                    'bucket-prefix': bucket_prefix,
                    'bucket-user': bucket_user,
                    'debug-prints': debug_prints,
                    'object-name': 'mana',
                    'path-replacers': {
                        'name': 'key'
                    },
                    'path-names': [],
                    'overwrite': False
                },
                object_data = None,
                object_metadata = None 
            )
     
    if store_action == 'modify':
        object_key = storage_parameters['object-key']
        object_input = storage_parameters['object-input']
        object_name = object_key + '.pkl'
        stored_object = object_storage_interaction(
            storage_client = swift_client,
            lock_parameters = storage_parameters['lock'],
            lock_location = storage_parameters['airflow-lock-location'],
            parameters = {
                'mode': 'get',
                'bucket-target': bucket_target,
                'bucket-prefix': bucket_prefix,
                'bucket-user': bucket_user,
                'debug-prints': debug_prints,
                'object-name': 'mana',
                'path-replacers': {
                    'name': object_name
                },
                'path-names': [],
                'overwrite': False
            },
            object_data = None,
            object_metadata = None
        )
        
        object_data = pickle.loads(stored_object[0])
        object_metadata = stored_object[2]
        print(object_data)
        print(object_input)
        
        stored_data = update_nested_dict(
            target_dict = object_data,
            update_dict = object_input
        )
        print(stored_data)
        object_metadata['version'] = object_metadata['version'] + 1
        stored_metadata = object_metadata
    
    object_stored = False
    if 0 < len(stored_data):
        stored_data = time_orch_update(
            storage_parameters = storage_parameters,
            orch_dict = stored_data
        )
             
        object_name = object_key + '.pkl'
        formatted_stored_data = pickle.dumps(stored_data)
        object_stored = object_storage_interaction(
            storage_client = swift_client,
            lock_parameters = storage_parameters['lock'],
            lock_location = storage_parameters['airflow-lock-location'],
            parameters = {
                'mode': 'send',
                'bucket-target': bucket_target,
                'bucket-prefix': bucket_prefix,
                'bucket-user': bucket_user,
                'debug-prints': debug_prints,
                'object-name': 'mana',
                'path-replacers': {
                    'name': object_name
                },
                'path-names': [],
                'overwrite': True
            },
            object_data = formatted_stored_data,
            object_metadata = stored_metadata
        )

        if 'airflow-cache-location' in storage_parameters:
            location = storage_parameters['airflow-cache-location']
            cache_parameters = storage_parameters['cache'][location]
            cache_key = storage_parameters['cache-key']
            cache_response = caching_save_dict(
                cache_parameters = cache_parameters,
                cache_key = cache_key,
                nested_dict = {
                    'object-stored': object_stored,
                    'object-key': object_key
                }
            )
    return object_stored
# Check imports and inputs
def storage_action_logs_interaction(
    swift_client: any,
    bucket_parameters: any,
    storage_parameters: any
) -> bool:
    try:
        import pandas as pd
        from icebreaker.storage.management import object_storage_interaction
        from icebreaker.pyarrow.use import pyarrow_serialize_dataframe
        from icebreaker.slurm.utility import slurm_format_logs
    except ImportError as e:
        raise ImportError("interaction-dags/sub_func/storage failed to import", e)

    store_action = storage_parameters['store-action']
    bucket_target = bucket_parameters['target']
    bucket_prefix = bucket_parameters['prefix']
    bucket_user = bucket_parameters['user']
    debug_prints = storage_parameters['debug-prints']
   
    stored_data = None
    object_name = ''
    if store_action == 'create':
        data_path = storage_parameters['file-path']
        log_list = slurm_format_logs(
            file_path = data_path
        )
        log_df = pd.DataFrame({'rows': log_list})

        if '.parquet' in data_path:
            stored_data = pyarrow_serialize_dataframe(
                dataframe = log_df
            )
        
        object_name = data_path.split('/')[-1]
        
    object_stored = False
    if 0 < len(object_name) and not stored_data is None:
        stored_metadata = {'version': 1}
        object_stored = object_storage_interaction(
            storage_client = swift_client,
            lock_parameters = storage_parameters['lock'],
            lock_location = storage_parameters['airflow-lock-location'],
            parameters = {
                'mode': 'send',
                'bucket-target': bucket_target,
                'bucket-prefix': bucket_prefix,
                'bucket-user': bucket_user,
                'debug-prints': debug_prints,
                'object-name': 'logs',
                'path-replacers': {
                    'name': object_name
                },
                'path-names': [],
                'overwrite': True
            },
            object_data = stored_data,
            object_metadata = stored_metadata
        )
    
    return object_stored
# Check imports and inputs
def storage_action_metrics_interaction(
    swift_client: any,
    bucket_parameters: any,
    storage_parameters: any
) -> bool:
    try:
        import pandas as pd
        from icebreaker.storage.management import object_storage_interaction
        from icebreaker.pyarrow.use import pyarrow_serialize_dataframe
        from icebreaker.slurm.utility import slurm_format_sacct, slurm_fix_sacct
    except ImportError as e:
        raise ImportError("interaction-dags/sub_func/storage failed to import", e)

    store_action = storage_parameters['store-action']
    bucket_target = bucket_parameters['target']
    bucket_prefix = bucket_parameters['prefix']
    bucket_user = bucket_parameters['user']
    debug_prints = storage_parameters['debug-prints']
   
    stored_data = None
    object_name = ''
    if store_action == 'create':
        data_path = storage_parameters['file-path']
        sacct_dict = slurm_format_sacct(
            file_path = data_path
        )
        fixed_sacct = slurm_fix_sacct(
            sacct_dict = sacct_dict,
            column_types = {
                'job-id': 'str',
                'job-name': 'str',
                'account': 'str',
                'partition': 'str',
                'req-cpus': 'int', 
                'alloc-cpus': 'int',
                'req-nodes': 'int',
                'alloc-nodes': 'int',
                'state': 'str',
                'ave-cpu-seconds': 'float',
                'ave-cpu-freq-khz': 'int',
                'ave-disk-read-bytes': 'int',
                'ave-disk-write-bytes': 'int',
                'timelimit-seconds': 'float',
                'submit-time': 'int',
                'start-time': 'int',
                'elapsed-seconds': 'float',
                'planned-seconds': 'float',
                'end-time': 'int',
                'planned-cpu-seconds': 'float',
                'cpu-time-seconds': 'float',
                'total-cpu-seconds': 'float'
            },
            value_replacers = {
                'str': 'null',
                'int': 0,
                'float': 0.0
            }
        )

        sacct_df = pd.DataFrame.from_dict(fixed_sacct)
        column_order = [
            'job-id',
            'job-name',
            'account',
            'partition', 
            'state',
            'req-cpus', 
            'alloc-cpus', 
            'req-nodes', 
            'alloc-nodes',
            'ave-cpu-freq-khz',
            'ave-disk-read-bytes', 
            'ave-disk-write-bytes', 
            'submit-time', 
            'start-time',
            'end-time',
            'timelimit-seconds', 
            'ave-cpu-seconds',
            'elapsed-seconds', 
            'planned-seconds', 
            'planned-cpu-seconds',
            'cpu-time-seconds', 
            'total-cpu-seconds'
        ]
        sacct_df = sacct_df.reindex(columns = column_order)

        if '.parquet' in data_path:
            stored_data = pyarrow_serialize_dataframe(
                dataframe = sacct_df
            )
        
        object_name = data_path.split('/')[-1]
        
    object_stored = False
    if 0 < len(object_name) and not stored_data is None:
        stored_metadata = {'version': 1}
        object_stored = object_storage_interaction(
            storage_client = swift_client,
            lock_parameters = storage_parameters['lock'],
            lock_location = storage_parameters['airflow-lock-location'],
            parameters = {
                'mode': 'send',
                'bucket-target': bucket_target,
                'bucket-prefix': bucket_prefix,
                'bucket-user': bucket_user,
                'debug-prints': debug_prints,
                'object-name': 'arti',
                'path-replacers': {
                    'name': 'SACCT'
                },
                'path-names': [
                    object_name
                ],
                'overwrite': True
            },
            object_data = stored_data,
            object_metadata = stored_metadata
        )
    return object_stored