def ray_setup_client(
    dashboard_address: str,
    loop_timeout: int,
    test_timeout: int,
    wait_timeout: int
):
    try:
        import time as t
        from ray.job_submission import JobSubmissionClient
        from ..misc.general import test_url
    except ImportError as e:
        raise ImportError("Failed to import", e)

    start = t.time()
    ray_client = None
    ray_dashboard_url = 'http://' + dashboard_address
    while t.time() - start <= loop_timeout:
        ray_exists = test_url(
            target_url = ray_dashboard_url,
            timeout = test_timeout
        )
        if ray_exists:
            ray_client = JobSubmissionClient(
                address = ray_dashboard_url
            )
            break
        t.sleep(wait_timeout)
    return ray_client

def ray_store_job(
    storage_client: any,
    storage_parameters: any,
    ray_runtime: any
):
    try:
        import os
        import time as t
        from ..storage.management import object_storage_interaction
    except ImportError as e:
        raise ImportError("Failed to import", e)

    start_time = t.time()
    working_directory_path = ray_runtime['working_dir']
    directory_name = working_directory_path.split('/')[-1]
    for root, dirs, files in os.walk(working_directory_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            object_path = []
            directory_found = False
            for name in file_path.split('/'):
                if name == directory_name:
                    directory_found = True
                if directory_found:
                    object_path.append(name)
            with open(file_path, 'rb') as stored_data:
                stored_metadata = {'version': 1}
                object_stored = object_storage_interaction(
                    storage_client = storage_client,
                    parameters = {
                        'mode': 'send',
                        'bucket-target': storage_parameters['bucket-target'],
                        'bucket-prefix': storage_parameters['bucket-prefix'],
                        'bucket-user': storage_parameters['bucket-user'],
                        'object-name': 'code',
                        'path-replacers': {
                            'name': 'RAY'
                        },
                        'path-names': object_path,
                        'overwrite': True,
                        'debug-prints': True,
                        'lock-parameters': {},
                        'lock-location': ''
                    },
                    object_data = stored_data,
                    object_metadata = stored_metadata
                ) 
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return total_time
            
def ray_download_job(
    storage_client: any,
    storage_parameters: any,
    ray_runtime: any
):
    try:
        import os
        from pathlib import Path
        import time as t
        from ..storage.management import object_storage_interaction
    except ImportError as e: 
        raise ImportError("Failed to import", e)

    start_time = t.time()

    object_stored = object_storage_interaction(
        storage_client = storage_client,
        parameters = {
            'mode': 'list',
            'bucket-target': storage_parameters['bucket-target'],
            'bucket-prefix': storage_parameters['bucket-prefix'],
            'bucket-user': storage_parameters['bucket-user'],
            'object-name': 'root',
            'path-replacers': {
                'name': 'key'
            },
            'path-names': [],
            'overwrite': True,
            'debug-prints': True,
            'lock-parameters': {},
            'lock-location': ''
        },
        object_data = None,
        object_metadata = None
    ) 

    working_directory_path = ray_runtime['working_dir']
    runtime_requirements = None
    if not isinstance(ray_runtime['pip'], list):
        runtime_requirements = ray_runtime['pip'].split('/')[-1]
    directory_name = working_directory_path.split('/')[-1]
    download_path = './downloads/ray'
    final_requirements = None
    runtime_directory = str(Path(download_path + '/' + directory_name))
    if not object_stored is None:
        for object_path, values in object_stored.items():
            if 'CODE' in object_path:
                if directory_name in object_path:
                    file_path_split = object_path.split('/')[2:]
                    file_directory_path = '/'.join(file_path_split)
                    
                    local_file_path = Path(download_path + '/' + file_directory_path)
                    local_file_path.parent.mkdir(parents=True, exist_ok=True)   
                    if runtime_requirements in str(local_file_path):
                        final_requirements = str(local_file_path)

                    if not local_file_path.exists():
                        file_object = object_storage_interaction(
                            storage_client = storage_client,
                            parameters = {
                                'mode': 'get',
                                'bucket-target': storage_parameters['bucket-target'],
                                'bucket-prefix': storage_parameters['bucket-prefix'],
                                'bucket-user': storage_parameters['bucket-user'],
                                'debug-prints': True,
                                'object-name': 'root',
                                'path-replacers': {
                                    'name': object_path
                                },
                                'path-names': [],
                                'overwrite': False,
                                'lock-parameters': {},
                                'lock-location': ''
                            }, 
                            object_data = None,
                            object_metadata = None
                        )
                        file_data = file_object[0]
                        with open(local_file_path, 'wb') as local_file:
                            local_file.write(file_data)
                    
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return runtime_directory, final_requirements