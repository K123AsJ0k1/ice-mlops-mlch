def workflow_setup_enviroment(
    env_path: str,
    swift_auth_url: str,
    swift_auth_version: str,
    swift_pre_auth_url: str
):
    try:
        from decouple import Config,RepositoryEnv
        from icebreaker.swift.setup import swift_get_parameters, swift_setup_client, swift_renew_client
        import os
    except ImportError as e:
        raise ImportError("workflow/utility failed to import", e)

    env_dict = Config(RepositoryEnv(env_path))
    swift_credential_id = env_dict.get('CSC_PROJECT_1_CRED_ID')
    swift_credential_secret = env_dict.get('CSC_PROJECT_1_CRED_SECRET')
    swift_project_name = env_dict.get('CSC_PROJECT_1')
    swift_domain_name = env_dict.get('CSC_USER_DOMAIN_NAME')

    setup_swift_parameters = swift_get_parameters(
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
        swift_parameters = setup_swift_parameters
    )

    hf_token = env_dict.get('HF_TOKEN')
    os.environ['HF_TOKEN'] = hf_token

    return {
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
        raise ImportError("Failed to import", e)

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
        raise ImportError("Failed to import", e)

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


