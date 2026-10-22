

def objects_store_data(
    swift_client: any,
    storage_parameters: any,
    object_data: any,
    object_metadata: any
) -> bool:
    try:
        import pickle
        from ..storage.management import object_storage_interaction
        from ..pyarrow.use import pyarrow_serialize_dataframe
    except ImportError as e:
        raise ImportError("objects/use failed to import", e)
    
    stored_data = None
    if storage_parameters['object-serialization'] == 'pickle':
        print('Formatted to pickle')
        stored_data = pickle.dumps(object_data)
    if storage_parameters['object-serialization'] == 'parquet':
        print('Formatted to parquet')
        stored_data = pyarrow_serialize_dataframe(dataframe = object_data)
    if storage_parameters['object-serialization'] == 'serialized':
        stored_data = object_data
    stored_metadata = object_metadata
    if 0 == len(object_metadata):
        stored_metadata = {'version': 1}

    if stored_data is None:
        return False
    
    storage_parameters['mode'] = 'send'
    object_stored = object_storage_interaction(
        storage_client = swift_client,
        parameters = storage_parameters,
        object_data = stored_data,
        object_metadata = stored_metadata
    )

    return object_stored

def objects_get_data(
    swift_client: any,
    storage_parameters: any,
    dict_format: bool
) -> any:
    try:
        import pickle
        from ..storage.management import object_storage_interaction
        from ..pyarrow.use import pyarrow_deserialize_dataframe
    except ImportError as e:
        raise ImportError("objects/use failed to import", e)
    
    storage_parameters['mode'] = 'get'
    stored_object = object_storage_interaction(
        storage_client = swift_client,
        parameters = storage_parameters,
        object_data = None,
        object_metadata = None
    )

    object_data = None
    if storage_parameters['object-serialization'] == 'pickle':
        object_data = pickle.loads(stored_object[0])
    if storage_parameters['object-serialization'] == 'parquet':
        object_data = pyarrow_deserialize_dataframe(serialized_dataframe = stored_object[0])

    object_general_metadata = stored_object[1]
    object_custom_metadata = stored_object[2]

    formatted_data = None
    if dict_format:
        formatted_data = {
            'object-data': object_data,
            'general-metadata': object_general_metadata,
            'custom-metadata': object_custom_metadata
        }
    else:
        formatted_data = (
            object_data,
            object_general_metadata,
            object_custom_metadata
        )

    return formatted_data

def objects_nested_update(
    swift_client: any,
    storage_parameters: any,
    object_input: any
) -> bool:
    try:
        import pickle
        from ..storage.management import object_storage_interaction
        from ..misc.dict import update_nested_dict
    except ImportError as e:
        raise ImportError("objects/use failed to import", e)
    
    storage_parameters['mode'] = 'get'
    stored_object = object_storage_interaction(
        storage_client = swift_client,
        parameters = storage_parameters,
        object_data = None,
        object_metadata = None
    )

    object_data = None
    object_metadata = None
    if storage_parameters['object-serialization'] == 'pickle':
        object_data = pickle.loads(stored_object[0])
        object_metadata = stored_object[2]

    if object_data is None:
        return False
    
    updated_data = update_nested_dict(
        target_dict = object_data,
        update_dict = object_input
    )

    if 'version' in object_metadata:
        object_metadata['version'] = object_metadata['version'] + 1
    else:
        object_metadata = {'version': 1}
    stored_metadata = object_metadata

    stored_data = None
    if storage_parameters['object-serialization'] == 'pickle':
        stored_data = pickle.dumps(updated_data)

    if stored_data is None:
        return False

    storage_parameters['mode'] = 'send'
    object_stored = object_storage_interaction(
        storage_client = swift_client,
        parameters = storage_parameters,
        object_data = stored_data,
        object_metadata = stored_metadata
    )
    return object_stored

def objects_get_prefix_list(
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

def objects_get_listed_data(
    swift_client: any,
    storage_parameters: any,
    object_names: list
):
    object_list = []
    for object_name in object_names:
        storage_parameters['path-names'] = [
            object_name
        ]
        data_object = objects_get_data(
            swift_client = swift_client,
            storage_parameters = storage_parameters,
            dict_format = False
        )
        object_list.append(data_object[0])
    return object_list