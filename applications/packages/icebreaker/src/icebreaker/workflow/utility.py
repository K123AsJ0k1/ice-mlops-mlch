def workflow_setup_enviroment(
    env_path: str,
    swift_auth_url: str,
    swift_auth_version: str,
    swift_pre_auth_url: str
):
    try:
        from decouple import Config,RepositoryEnv
        from ..swift.setup import swift_get_parameters, swift_setup_client, swift_renew_client
        import os
    except ImportError as e:
        raise ImportError("workflow/utility failed to import", e)

    env_dict = Config(RepositoryEnv(env_path))
    swift_credential_id = env_dict.get('CSC_PROJECT_1_CRED_ID')
    swift_credential_secret = env_dict.get('CSC_PROJECT_1_CRED_SECRET')
    swift_project_name = env_dict.get('CSC_PROJECT_1')
    swift_domain_name = env_dict.get('CSC_USER_DOMAIN_NAME')

    swift_parameters = swift_get_parameters(
        secret_parameters = {
            'auth-url': swift_auth_url,
            'credential-id': swift_credential_id,
            'credential-secret': swift_credential_secret,
            'auth-version': swift_auth_version,
            'project-name': swift_project_name,
            'user-domain-name': swift_domain_name,
            'project-domain-name': swift_domain_name,
            'pre-auth-url': swift_pre_auth_url
        }
    )

    swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )

    required_keys = [
        'pre-auth-url',
        'pre-auth-token',
        'user-domain-name',
        'project-domain-name',
        'project-name',
        'auth-version'
    ]
    reduced_swift_parameters = {
        k: swift_parameters[k] for k in required_keys
    }

    hf_token = env_dict.get('HF_TOKEN')
    os.environ['HF_TOKEN'] = hf_token

    return {
        'swift-parameters': reduced_swift_parameters,
        'swift-client': swift_client,
        'hf-token': hf_token
    }

def workflow_format_material(
    material_data: any
) -> any:
    try:
        import copy 
        import pandas as pd
        from ..misc.dict import flatten_nested_dict
    except ImportError as e:
        raise ImportError("workflow/utility failed to import", e)

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
    
    return dataframe

def workflow_grade_row(
    data_row: any,
    path_column: str,
    global_reference_paths: dict,
    material_grades: dict
):
    row_absolute_path = data_row[path_column]
    file_type = row_absolute_path.split('.')[-1]

    row_grade = None
    if file_type in material_grades:
        m_type, row_grade = material_grades[file_type]
        if m_type == 'secondary':
            for _, absolute_path in global_reference_paths.items():
                if absolute_path == row_absolute_path:
                    row_grade += 1
                    break  
    return row_grade

def workflow_set_weights(
    target_df: any,
    group_columns: list,
    value_column: str,
    weight_column: str
): 
    weight_lookup = target_df.groupby(group_columns)[value_column].apply(list).to_dict()
        
    weights_batch = []
    for _, row in target_df.iterrows():
        group_key = tuple(row[column] for column in group_columns)
        relevant_id_batch = weight_lookup[group_key]
        relevant_weighed_ids = {}
        for relevant_id in relevant_id_batch:
            id_weight = target_df.loc[target_df[value_column] == relevant_id, weight_column].values[0]
            relevant_weighed_ids[relevant_id] = int(id_weight)
        
        weights_batch.append(relevant_weighed_ids)
    
    return weights_batch

def workflow_divide_external_data(
    dataset_repository: str,
    dataset_name: str,
    hf_token: str,
    table_size: int,
    size_limit: int,
    relevant_columns: list,
    renamed_columns: dict,
    path_prefix: str
) -> int:
    try:
        import time as t
        from pathlib import Path
        import pandas as pd
        import dask.dataframe as dd
        from datasets import load_dataset
    except ImportError as e:
        raise ImportError("workflow/utility failed to import", e)

    start_time = t.time()
    data_stream = load_dataset(
        dataset_repository, 
        dataset_name,
        split = 'train',
        streaming = True,
        token = hf_token
    )

    dask_dfs = []
    batch = []
    row_index = 0
    batch_index = 0
    for i, row in enumerate(data_stream):
        if size_limit <= (i + 1):
            break
        batch.append(row)
        row_index += 1
        if (row_index) % table_size == 0:
            batch_df = pd.DataFrame(batch) 
            dask_df = dd.from_pandas(batch_df, npartitions = 1)
            dask_dfs.append(dask_df)
            batch = []
            batch_index += 1
    if batch:
        batch_df = pd.DataFrame(batch) 
        dask_df = dd.from_pandas(batch_df, npartitions = 1)
        dask_dfs.append(dask_df)
        batch = []
        batch_index += 1
    processing_dask_df = dd.concat(dask_dfs)

    processing_dask_df = processing_dask_df[relevant_columns].rename(columns = renamed_columns)

    partitions = processing_dask_df.to_delayed()
    table_index = 1
    for i, partition in enumerate(partitions):
        file_path = f'{path_prefix}-{table_index}.parquet'

        absolute_file_path = Path(file_path).resolve()
        print(f'Storing partition into: {file_path}')
        computed_partition = partition.compute()
        computed_partition.to_parquet(absolute_file_path, engine = 'pyarrow')
        table_index += 1 
        
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print(f'Spent seconds: {total_time}')
    return total_time

def workflow_store_data(
    swift_client: any,
    storage_parameters: any,
    data_prefix: str,
    data_source: str,
    data_type: str
) -> int: 
    try:
        import os
        import json
        import time as t
        from pathlib import Path
        from ..objects.use import objects_store_data
    except ImportError as e:
        raise ImportError("workflow/utility failed to import", e)

    start_time = t.time()
    if data_type == 'internal':
       for root, dirs, files in os.walk(data_source):
           for file in files:
                file_path = os.path.join(root, file)
                absolute_file_path = Path(file_path).resolve()
                if '.json' in file_path:
                    data = None
                    with open(absolute_file_path, 'r', encoding = 'utf-8') as file:
                        data = json.load(file)
                    
                    dataframe = workflow_format_material(
                        material_data = data 
                    )

                    file_name = file_path.split('/')[-1].split('.')[0]            

                    path_name = f'{data_prefix}-{file_name}.pkl'
                    
                    storage_parameters['object-name'] = 'data'
                    storage_parameters['object-serialization'] = 'pickle'
                    storage_parameters['path-replacers'] = {
                        'name': 'SOURCE'
                    }
                    storage_parameters['path-names'] = [
                        path_name
                    ]
                    storage_parameters['debug-prints'] = True
                    storage_parameters['lock-parameters'] = {}
                    storage_parameters['lock-location'] = None
                    storage_parameters['overwrite'] = True
                    
                    object_stored = objects_store_data( 
                        swift_client = swift_client,
                        storage_parameters = storage_parameters,
                        object_data = dataframe,
                        object_metadata = {}
                    )
                    
    if data_type == 'external':
        for root, dirs, files in os.walk(data_source):
           for file in files:
                file_path = os.path.join(root, file)
                absolute_file_path = Path(file_path).resolve()
                if '.parquet' in file_path:
                    path_name = f'{data_prefix}-{file_path.split('/')[-1]}' 
                    
                    storage_parameters['object-name'] = 'data'
                    storage_parameters['object-serialization'] = 'serialized'
                    storage_parameters['path-replacers'] = {
                        'name': 'SOURCE'
                    }
                    storage_parameters['path-names'] = [
                        path_name
                    ]
                    storage_parameters['debug-prints'] = True
                    storage_parameters['lock-parameters'] = {}
                    storage_parameters['lock-location'] = None
                    storage_parameters['overwrite'] = True
                    
                    with open(absolute_file_path, 'rb') as stored_data:
                        object_stored = objects_store_data(
                            swift_client = swift_client,
                            storage_parameters = storage_parameters,
                            object_data = stored_data,
                            object_metadata = {}
                        )   
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return total_time

def workflow_store_models(
    storage_client: any,
    storage_parameters: any,
    file_parameters: any
) -> int:
    try:
        import os
        import time as t
        from pathlib import Path
        from ..storage.management import object_storage_interaction, storage_set_bucket_name, storage_set_object_path
        from ..swift.use import swift_define_object, swift_upload_objects
        from ..objects.use import objects_store_data
    except ImportError as e:
        raise ImportError("workflow/utility failed to import", e)

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
    upload_objects = []
    for root, dirs, files in os.walk(file_parameters['model-directory']):
        for file in files:
            file_path = os.path.join(root, file)
            if not '.cache' in file_path:
                file_type = file_path.split('.')[-1]
                model_name = file_path.split('/')[-2]  
                object_name = file_path.split('/')[-1] 

                file_exists = False
                for existing_path in object_stored.keys():
                    existing_object = existing_path.split('/')[-1]
                    if object_name == existing_object:
                        file_exists = True
                file_exists = False
                if not file_exists:
                    if 'json' == file_type:
                        model_name = file_path.split('/')[-2]  
                        object_name = file_path.split('/')[-1] 
                        if not 'download' == model_name:
                            print('Storing JSON file:', file_path)
                            with open(file_path, 'rb') as stored_data:
                                storage_parameters['object-name'] = 'root'
                                storage_parameters['object-serialization'] = 'serialized'
                                storage_parameters['path-replacers'] = {
                                    'name': 'MODELS'
                                }
                                storage_parameters['path-names'] = [
                                    model_name,
                                    object_name
                                ]
                                storage_parameters['debug-prints'] = True
                                storage_parameters['lock-parameters'] = {}
                                storage_parameters['lock-location'] = None
                                storage_parameters['overwrite'] = True

                                object_stored = objects_store_data(
                                    swift_client = storage_client,
                                    storage_parameters = storage_parameters,
                                    object_data = stored_data,
                                    object_metadata = {}
                                )

                        continue
                    if 'safetensors' == file_type or 'bin' == file_type:
                        print('Storing ', file_type, ' file:', file_path)
                        
                        object_path = storage_set_object_path(
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

                        absolute_local_path = str(Path(file_path).resolve())
                        upload_objects.append(
                            swift_define_object(
                                local_path = absolute_local_path,
                                object_path = object_path
                            )
                        )
                        continue
    
    bucket_name = storage_set_bucket_name(
        bucket_target = storage_parameters['bucket-target'],
        bucket_prefix = storage_parameters['bucket-prefix'],
        bucket_user = storage_parameters['bucket-user'],
        debug_prints = True
    )

    if 0 < len(upload_objects):
        swift_parameters = storage_parameters['swift-parameters']

        swift_options = {
            'auth_version': swift_parameters['auth-version'],
            'preauthtoken': swift_parameters['pre-auth-token'],
            'preauthurl': swift_parameters['pre-auth-url'],
            'os_user_domain_name': swift_parameters['user-domain-name'],
            'os_project_domain_name': swift_parameters['project-domain-name'],
            'os_project_name': swift_parameters['project-name'],
            'object_uu_threads': 4
        }
        #print(upload_objects)
        
        objects_uploaded = swift_upload_objects(
            swift_options = swift_options,
            bucket_name = bucket_name,
            object_list = upload_objects
        )
        
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return total_time

def workflow_sample_datasets(
    swift_client: any,
    fasttext_model: any,
    magika_model: any,
    storage_parameters: dict,
    sampling_details: dict
):
    try:
        import time as t
        import pandas as pd
        from ..objects.use import objects_get_data
        from ..fast_text.use import fasttext_get_languages
        from ..mgka.use import magika_get_formats
    except ImportError as e:
        raise ImportError("workflow/utility failed to import", e)
    
    start_time = t.time()

    name_prefix = sampling_details['prefix']
    data_serialization = sampling_details['serialization']
    dataset_parameters = sampling_details['parameters']
    accepted_languages = sampling_details['accepted-languages']
    accepted_formats = sampling_details['accepted-formats']
    
    sample_dfs = []
    for name, parameters in dataset_parameters.items():
        dataset_name = f'{name_prefix}-{name}'
        path_name = f'{dataset_name}.{data_serialization}'
        storage_parameters['path-names'] = [
            path_name
        ]

        data_object = objects_get_data(
            swift_client = swift_client,
            storage_parameters = storage_parameters,
            dict_format = False
        )  

        dataset_data = data_object[0]
        max_samples = parameters['max-samples']
        if parameters['type'] == 'complete':
            for key, value in max_samples.items():
                if key == parameters['format-default-label']:
                    sample_df = dataset_data.head(value).copy()
                    sample_df['language'] = parameters['language-default-label']
                    sample_df['language-confidence'] = 1.0
                    sample_df['format'] = key
                    sample_df['format-confidence'] = 1.0
                    sample_df['format-counts'] = {}
                    sample_df['dataset'] = dataset_name
                    sample_df['dataset-idx'] = list(range(value))
                    sample_dfs.append(sample_df)

        if parameters['type'] == 'mixed':
            search_limit = parameters['search-limit']
            print(f'Search limit: {search_limit}')
            unfiltered_df = dataset_data.head(search_limit)

            language_column = parameters['language-column']
            language_default_label = parameters['language-default-label']
            language_confidence_threshold = parameters['language-confidence-threshold']

            predicted_languages = fasttext_get_languages(
                model = fasttext_model,
                texts = unfiltered_df[language_column].tolist(),
                default_label = language_default_label,
                confidence_threshold = language_confidence_threshold,
                label_replacer = {}
            )
            
            print(f'Language defaults: {predicted_languages['default-amount']}')

            format_column = parameters['format-column']
            format_default_label = parameters['format-default-label']
            format_confidence_threshold = parameters['format-confidence-threshold']

            predicted_formats = magika_get_formats(
                model = magika_model,
                texts = unfiltered_df[format_column].tolist(),
                default_label = format_default_label,
                confidence_threshold = format_confidence_threshold,
                label_replacer = {}
            )
            
            print(f'Format defaults: {predicted_formats['default-amount']}')
            wanted_rows = []
            selected_languages = []
            selected_language_confidences = []
            selected_formats = []
            selected_format_confidences = []
            selected_format_counts = []
            
            row_idx = 0
            for language_tuple in predicted_languages['predictions']:
                predicted_language = language_tuple[0]
                prediction_confidence = language_tuple[1]
                if predicted_language in accepted_languages:
                    if len(wanted_rows) < max_samples['general']:
                        format_tuple = predicted_formats['predictions'][row_idx]
                        format_label = format_tuple[0]
                        format_confidence = format_tuple[1]
                        format_counts = format_tuple[2]

                        #correct_formats = False
                        #for format_type in parameters[]

                        # Filter txt
                        # Filter anything that isn't sh, bash or python

                        #wanted_rows.append(row_idx)
                        #selected_languages.append(predicted_language)
                        #selected_language_confidences.append(prediction_confidence)
                        #selected_formats.append(format_tuple[0])
                        #selected_format_confidences.append(format_tuple[1])
                        #selected_format_counts.append(format_tuple[2])
                    else:
                        break
                row_idx += 1
            
            sample_df = unfiltered_df.iloc[wanted_rows].copy()
            print(selected_languages)
            print(selected_format_counts)
            sample_df['language'] = selected_languages
            sample_df['language-confidence'] = selected_language_confidences
            sample_df['format'] = selected_formats
            sample_df['format-confidence'] = selected_format_confidences
            sample_df['format-counts'] = selected_format_counts
            sample_df['dataset'] = dataset_name
            sample_df['dataset-idx'] = wanted_rows 
            sample_dfs.append(sample_df)           

    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)

    complete_dataframe = pd.concat(sample_dfs, ignore_index = True)

    return complete_dataframe
