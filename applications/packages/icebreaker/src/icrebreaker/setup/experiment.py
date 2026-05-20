
def experiment_format_material(
    material_data: any
) -> any:
    try:
        import copy 
        import pickle
        import pandas as pd
    except ImportError as e:
        raise ImportError("Failed to import", e)

    dict_list = []
    document_index = 1
    for document in material_data:
        for chunk in document:
            modified_chunk = copy.deepcopy(chunk)
            for key, value in modified_chunk.items():
                if isinstance(value, dict):
                    if 0 < len(value):
                        modified_chunk[key] = flatten_nested_dict(
                            target_dict = value,
                            parent_key = '',
                            seperator = '|'
                        )
            modified_chunk['document'] = document_index
            dict_list.append(modified_chunk)
        document_index += 1

    column_order = [
        'part',
        'document',
        'chapter',
        'index',
        'strategy',
        'header',
        'topic',
        'absolute-path',
        'metadata',
        'content',
        'rows',
        'characters',
        'ref-material',
        'ref-paths'
    ]

    dataframe = pd.DataFrame(dict_list, columns = column_order)
    stored_data = pickle.dumps(dataframe)

    return stored_data

def experiment_store_data(
    storage_client: any,
    file_parameters: any,
    data_type: str
) -> int: 
    try:
        import os
        import json
        import time as t
        from ..storage.management import object_storage_interaction, set_object_path, set_bucket_name
    except ImportError as e:
        raise ImportError("Failed to import", e)

    start_time = t.time()
    if data_type == 'internal':
       for root, dirs, files in os.walk(file_parameters['data-source']):
           for file in files:
                file_path = os.path.join(root, file)
                if '.json' in file_path:
                    data = None
                    with open(file_path, 'r', encoding = 'utf-8') as file:
                        data = json.load(file)
                    stored_metadata = {'version': 1}

                    stored_data = experiment_format_material(
                        material_data = data 
                    )

                    print('Storing file in path: ', file_path)

                    file_name = file_path.split('/')[-1].split('.')[0]            

                    object_name = file_parameters['object-prefix'] + '-' + file_name + '.pkl'
                    object_stored = object_storage_interaction(
                        storage_client = storage_client,
                        parameters = {
                            'mode': 'send',
                            'bucket-target': file_parameters['bucket-target'],
                            'bucket-prefix': file_parameters['bucket-prefix'],
                            'bucket-user': file_parameters['bucket-user'],
                            'object-name': 'data',
                            'path-replacers': {
                                'name': 'SOURCE'
                            },
                            'path-names': [
                                object_name
                            ],
                            'overwrite': True
                        },
                        object_data = stored_data,
                        object_metadata = stored_metadata
                    )   
    if data_type == 'external':
        for root, dirs, files in os.walk(file_parameters['data-source']):
           for file in files:
                file_path = os.path.join(root, file)
                if '.parquet' in file_path:
                    stored_metadata = {'version': 1}
                    print('Storing file in path: ', file_path)
                    object_name = file_path.split('/')[-1]   
                    with open(file_path, 'rb') as stored_data:
                        object_stored = object_storage_interaction(
                            storage_client = storage_client,
                            parameters = {
                                'mode': 'send',
                                'bucket-target': file_parameters['bucket-target'],
                                'bucket-prefix': file_parameters['bucket-prefix'],
                                'bucket-user': file_parameters['bucket-user'],
                                'object-name': 'data',
                                'path-replacers': {
                                    'name': 'SOURCE'
                                },
                                'path-names': [
                                    object_name
                                ],
                                'overwrite': True
                            },
                            object_data = stored_data,
                            object_metadata = stored_metadata
                        )   
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return total_time

def experiment_store_models(
    storage_client: any,
    storage_parameters: any,
    file_parameters: any
) -> int:
    try:
        import os
        import time as t
        from ..storage.management import object_storage_interaction, set_object_path, set_bucket_name
        from ..swift.use import swift_define_object, swift_upload_objects
    except ImportError as e:
        raise ImportError("Failed to import", e)

    start_time = t.time()

    object_stored = object_storage_interaction(
        storage_client = storage_client,
        lock_parameters = {},
        lock_location = 'no-lock',
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
            'debug-prints': False
        },
        object_data = None,
        object_metadata = None
    ) 
    upload_objects = []
    for root, dirs, files in os.walk(file_parameters['model-directory']):
        for file in files:
            file_path = os.path.join(root, file)
            print(file_path)
            if not '.cache' in file_path:
                file_type = file_path.split('.')[-1]
                model_name = file_path.split('/')[-2]  
                object_name = file_path.split('/')[-1] 

                file_exists = False
                for existing_path in object_stored.keys():
                    existing_object = existing_path.split('/')[-1]
                    if object_name == existing_object:
                        file_exists = True

                if not file_exists:
                    if 'json' == file_type:
                        stored_metadata = {'version': 1}
                        model_name = file_path.split('/')[-2]  
                        object_name = file_path.split('/')[-1] 
                        if not 'download' == model_name:
                            print('Storing JSON file:', file_path)
                            with open(file_path, 'rb') as stored_data:
                                object_stored = object_storage_interaction(
                                    storage_client = storage_client,
                                    lock_parameters = {},
                                    lock_location = 'no-lock',
                                    parameters = {
                                        'mode': 'send',
                                        'bucket-target': storage_parameters['bucket-target'],
                                        'bucket-prefix': storage_parameters['bucket-prefix'],
                                        'bucket-user': storage_parameters['bucket-user'],
                                        'object-name': 'root',
                                        'path-replacers': {
                                            'name': 'MODELS'
                                        },
                                        'path-names': [
                                            model_name,
                                            object_name
                                        ],
                                        'overwrite': True,
                                        'debug-prints': True
                                    },
                                    object_data = stored_data,
                                    object_metadata = stored_metadata
                                ) 
                        continue
                    if 'safetensors' == file_type or 'bin' == file_type:
                        print('Storing ', file_type, ' file:', file_path)
                        
                        object_path = set_object_path(
                            object_name = 'root',
                            path_replacers = {
                                'name': 'MODELS'
                            },
                            path_names = [
                                model_name,
                                object_name 
                            ],
                            debug_prints = True
                        )
                        
                        upload_objects.append(
                            swift_define_object(
                                local_path = file_path,
                                object_path = object_path
                            )
                        )
                        continue
    
    bucket_name = set_bucket_name(
        bucket_target = storage_parameters['bucket-target'],
        bucket_prefix = storage_parameters['bucket-prefix'],
        bucket_user = storage_parameters['bucket-user'],
        debug_prints = True
    )

    if 0 < len(upload_objects):
        swift_options = storage_parameters['swift-options']
        objects_uploaded = swift_upload_objects(
            swift_options = swift_options,
            bucket_name = bucket_name,
            object_list = upload_objects
        )

    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return total_time