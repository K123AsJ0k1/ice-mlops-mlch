
def data_list_objects(
    storage_client: any,
    storage_parameters: any,
    object_prefix: str
): 
    try:
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

    prefix_objects = []
    if not object_stored is None:
        for object_path, values in object_stored.items():
            if object_prefix in object_path:
                used_bytes = values['used-bytes']
                object_tuple = (object_path, used_bytes)
                prefix_objects.append(object_tuple)
            
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return prefix_objects