

def objects_store_data(
    swift_client: any,
    storage_parameters: any,
    object_data: any
) -> bool:
    try:
        import pickle
        from ..storage.management import object_storage_interaction
    except ImportError as e:
        raise ImportError("clusters/use failed to import", e)
    
    stored_data = None
    if storage_parameters['object-serialization'] == 'pickle':
        print('Formatted to pickle')
        stored_data = pickle.dumps(object_data)
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
        raise ImportError("clusters/use failed to import", e)
    
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
        raise ImportError("clusters/use failed to import", e)
    
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
    object_metadata['version'] = object_metadata['version'] + 1
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