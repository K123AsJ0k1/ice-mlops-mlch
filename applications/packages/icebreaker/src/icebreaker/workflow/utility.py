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
            absolute_local_path = str(Path(file_path).resolve())
            if not '.cache' in absolute_local_path:
                file_type = absolute_local_path.split('.')[-1]
                model_name = absolute_local_path.split('/')[-2]  
                object_name = absolute_local_path.split('/')[-1] 

                file_exists = False
                for existing_path in object_stored.keys():
                    existing_object = existing_path.split('/')[-1]
                    if object_name == existing_object:
                        file_exists = True
                file_exists = False
                if not file_exists:
                    if 'json' == file_type or 'bin' == file_type:
                        model_name = absolute_local_path.split('/')[-2]  
                        object_name = absolute_local_path.split('/')[-1] 
                        if not 'download' == model_name:
                            print(f'Storing {file_type} file: {absolute_local_path}')
                            with open(absolute_local_path, 'rb') as stored_data:
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
                    if 'safetensors' == file_type:
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
                        # There is some kind of problem with fasttext
                        upload_objects.append(
                            swift_define_object(
                                local_path = file_path,
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
        # There is some kind of problem with fasttext
        # This gets a bytes-like object is required, not 'str' for fasttext
        
        objects_uploaded = swift_upload_objects(
            swift_options = swift_options,
            bucket_name = bucket_name,
            object_list = upload_objects
        )
        
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return total_time

def workflow_time_stats(
    time_df: any,
    cluster_yaml: dict
) -> any:
    try:
        from ..misc.dict import get_dict_value
    except ImportError as e:
        raise ImportError("workflow/utility failed to import", e)
    
    # infra names are local-lt or cloud-vm
    # step names are step or step-n with first one being step-0
    
    formatted_tables = []
    formatted_df = time_df.copy()
    formatted_df = formatted_df.rename(columns = {'total':'time'})
    formatted_df['infrastructure'] = formatted_df['name'].str.extract(r'(local-lt\d+|cloud-vm\d+)', expand=False)
    formatted_df['stage'] = formatted_df['name'].str.extract(r'(step-\d+|step\b)', expand=False).fillna('step')

    infra_cost = {}
    for name in formatted_df['infrastructure'].unique():
        name_split = name.split('-')
        used_key = f'{name_split[0]}-clusters-{name_split[-1]}'
        infra_cost[name] = get_dict_value(
            target_dict = cluster_yaml,
            key_path = used_key,
            separator = '-'
        )['utilization-cost-sec']

    costs = []
    total_times = formatted_df['time'].to_list()
    index = 0
    for name in formatted_df['infrastructure'].to_list():
        total_cost = total_times[index] * infra_cost[name] 
        costs.append(total_cost)
        index += 1
    formatted_df['cost'] = costs

    formatted_tables.append(formatted_df)

    group_columns = [
        'infrastructure',
        'stage'
    ]

    target_columns = [
        'time',
        'cost'
    ]

    wanted_stats = [
        'sum',
        'mean', 
        'std', 
        'median', 
        'min', 
        'max'
    ]

    formatted_metrics = {}
    
    for single_group in group_columns:
        df_stats = formatted_df.groupby(single_group)[target_columns].agg(wanted_stats)
        formatted_tables.append(df_stats)
        for tuple, values in df_stats.to_dict().items():
            for group_case, stat_value in values.items():
                flattened_key = f'{group_case}-{tuple[0]}-{tuple[1]}'
                formatted_metrics[flattened_key] = stat_value

    df_stats = formatted_df.groupby(group_columns)[target_columns].agg(wanted_stats)
    formatted_tables.append(df_stats)

    local_runner_cost = formatted_df[formatted_df['infrastructure'].isin(['local-lt1'])]['cost'].max()

    cloud_runner = formatted_df[formatted_df['infrastructure'].isin(['cloud-vm1'])]['cost']
    cloud_runner_cost = cloud_runner.iloc[0] + cloud_runner.max()

    remaining_df = formatted_df[~formatted_df['infrastructure'].isin(['local-lt1', 'cloud-vm1'])]

    collective_cots = remaining_df['cost'].sum()
    pipeline_cost = local_runner_cost + cloud_runner_cost + collective_cots

    formatted_metrics['total-pipeline-cost-eur'] = float(pipeline_cost)

    return {
        'metrics': formatted_metrics,
        'tables': formatted_tables
    }

def workflow_create_validation_dataset(
    swift_client: any,
    mlflow_client: any,
    dataset_paths: list,
    storage_parameters: dict,
    experiment_name: str,
    dataset_tags: dict,
    dataset_user: str
):
    try: 
        import json
        import pandas as pd
        from ..objects.use import objects_get_data, objects_store_data
        from ..mlflow.use import mlflow_create_dataset, mlflow_get_or_create_experiment
    except ImportError as e:
        raise ImportError("workflow/utility failed to import", e)

    joined_dataframes = []
    for dataset_path in dataset_paths:
        data_object = objects_get_data(
            swift_client = swift_client,
            storage_parameters = {
                'bucket-target': storage_parameters['bucket-target'],
                'bucket-prefix': storage_parameters['bucket-prefix'],
                'bucket-user': storage_parameters['bucket-user'],
                'object-name': 'root',
                'object-serialization': storage_parameters['object-serialization'],
                'path-replacers': {
                    'name': dataset_path
                },
                'path-names': [],
                'debug-prints': True,
                'lock-parameters': {},
                'lock-location': None,
                'overwrite': True
            },
            dict_format = False
        ) 

        object_df = data_object[0]
        selected_dataframe = object_df[object_df['relevance'] == 3]
        joined_dataframes.append(selected_dataframe)

    validation_dataset = pd.concat(joined_dataframes)
    validation_dataset['ranking-weights'] = validation_dataset['ranking-weights'].apply(json.dumps)

    dataset_name = 'internal-validation-dataset'
    path_name = f'{dataset_name}.parquet'
    storage_parameters['object-name'] = 'data'
    storage_parameters['object-serialization'] = 'parquet'
    storage_parameters['path-replacers'] = {
        'name': 'EVALUTION'
    }
    storage_parameters['path-names'] = [
        path_name
    ]
    storage_parameters['debug-prints'] = True
    storage_parameters['lock-parameters'] = {}
    storage_parameters['lock-location'] = None
    storage_parameters['overwrite'] = True

    dataset_stored = objects_store_data(
        swift_client = swift_client,
        storage_parameters = storage_parameters,
        object_data = validation_dataset,
        object_metadata = {}
    )

    experiment_id = mlflow_get_or_create_experiment(
        mlflow_client = mlflow_client,
        name = experiment_name
    ) 

    formatted_records = []
    for _, row in validation_dataset.iterrows():
        formatted_records.append({
            'inputs': {
                'question': row['topic']
            },
            'expectations': {
                'ground_truth': row['content'],
                'part': row['part'],
                'chapter': row['chapter'],
                'idx': row['idx'],
                'characters': row['characters'],
                'relevance': row['relevance'],
                'weights': row['ranking-weights']
            },
            'source': {
                'source_type': 'HUMAN'
            },
            'tags': {
                'mlflow.user': dataset_user
            }
        })
    
    dataset_tags['mlflow.user'] = dataset_user
    dataset_id = mlflow_create_dataset(
        mlflow_client = mlflow_client,
        dataset_name = dataset_name,
        experiment_id = experiment_id,
        dataset_tags = dataset_tags,
        dataset_records = formatted_records
    )

    return {
        'dataset': validation_dataset,
        'id': dataset_id
    }

def workflow_create_general_dataset(
    swift_client: any,
    mlflow_client: any,
    sampling_parameters: dict,
    storage_parameters: dict,
    dataset_paths: list,
    experiment_name: str,
    dataset_tags: dict,
    dataset_user: str
):
    try: 
        import json
        import random
        import pandas as pd
        from ..objects.use import objects_get_data, objects_store_data
        from ..mlflow.use import mlflow_create_dataset, mlflow_get_or_create_experiment
    except ImportError as e:
        raise ImportError("workflow/utility failed to import", e)

    used_parameters = sampling_parameters['sampling']

    random.seed(used_parameters.get('seed', 42))
    wanted_samples = used_parameters.get('wanted-samples', {})
    datasets_meta = used_parameters.get('datasets', {})

    # Step 1: Map each format to the list of datasets that support it
    format_to_datasets = {}
    for ds_name, meta in datasets_meta.items():
        formats = meta.get("format-samples", [])
        for fmt in formats:
            if fmt not in format_to_datasets:
                format_to_datasets[fmt] = []
            format_to_datasets[fmt].append(ds_name)
    
    # Step 2: Calculate target sample quotas per dataset
    dataset_quotas = {ds_name: {} for ds_name in datasets_meta.keys()}
    for fmt, target_count in wanted_samples.items():
        eligible_datasets = format_to_datasets.get(fmt, [])
        if not eligible_datasets or target_count <= 0:
            continue

        # Distribute the format's wanted-samples evenly across eligible datasets
        base = target_count // len(eligible_datasets)
        remainder = target_count % len(eligible_datasets)

        for i, ds_name in enumerate(eligible_datasets):
            share = base + (1 if i < remainder else 0)
            if not fmt in dataset_quotas[ds_name]:
                dataset_quotas[ds_name][fmt] = 0
            dataset_quotas[ds_name][fmt] += share
    
    accepted_language = used_parameters.get('accepted-language', 'en')
    joined_rows = []
    for dataset_path in dataset_paths:
        data_object = objects_get_data(
            swift_client = swift_client,
            storage_parameters = {
                'bucket-target': storage_parameters['bucket-target'],
                'bucket-prefix': storage_parameters['bucket-prefix'],
                'bucket-user': storage_parameters['bucket-user'],
                'object-name': 'root',
                'object-serialization': storage_parameters['object-serialization'],
                'path-replacers': {
                    'name': dataset_path
                },
                'path-names': [],
                'debug-prints': True,
                'lock-parameters': {},
                'lock-location': None,
                'overwrite': True
            },
            dict_format = False
        ) 

        object_df = data_object[0]
        
        dataset_name = dataset_path.split('external-')[-1].split('.')[0]
        language_filter = object_df[object_df['language'] == accepted_language]
        accepted_formats = dataset_quotas[dataset_name].keys()
        for format, number in dataset_quotas[dataset_name].items():
            #format_filter = language_filter[(language_filter['format'] == format) & (language_filter['format-confidence'] == 1.0)]
            format_filter = language_filter[language_filter['format'] == format]
            sampled = 0
            for index, row in format_filter.iterrows():
                format_counts = json.loads(row['format-counts'])
                format_check = True
                for found_format in format_counts.keys():
                    if not found_format in accepted_formats:
                        format_check = False

                if format_check:
                    modified_row = row.copy()
                    modified_row['dataset-index'] = index 
                    modified_row['dataset-path'] = dataset_path
                    if sampled < number:
                        joined_rows.append(modified_row)
                        sampled += 1
                        
    general_dataset = pd.DataFrame(joined_rows)
    general_dataset = general_dataset.reset_index(drop = True)

    dataset_name = 'external-general-dataset'
    path_name = f'{dataset_name}.parquet'
    storage_parameters['object-name'] = 'data'
    storage_parameters['object-serialization'] = 'parquet'
    storage_parameters['path-replacers'] = {
        'name': 'EVALUTION'
    }
    storage_parameters['path-names'] = [
        path_name
    ]
    storage_parameters['debug-prints'] = True
    storage_parameters['lock-parameters'] = {}
    storage_parameters['lock-location'] = None
    storage_parameters['overwrite'] = True

    dataset_stored = objects_store_data(
        swift_client = swift_client,
        storage_parameters = storage_parameters,
        object_data = general_dataset,
        object_metadata = {}
    )

    experiment_id = mlflow_get_or_create_experiment(
        mlflow_client = mlflow_client,
        name = experiment_name
    ) 

    formatted_records = []
    for _, row in general_dataset.iterrows():
        formatted_records.append({
            'inputs': {
                'question': row['question']
            },
            'expectations': {
                'ground_truth': row['answer'],
                'format': row['format'],
                'format_counts': row['format-counts'],
                'question-characters': row['question-characters'],
                'answer-characters': row['answer-characters'],
                'dataset-path': row['dataset-path'],
                'dataset-index': row['dataset-index']
            },
            'source': {
                'source_type': 'UNSPECIFIED'
            },
            'tags': {
                'mlflow.user': dataset_user
            }
        })
    
    dataset_tags['mlflow.user'] = dataset_user
    dataset_id = mlflow_create_dataset(
        mlflow_client = mlflow_client,
        dataset_name = dataset_name,
        experiment_id = experiment_id,
        dataset_tags = dataset_tags,
        dataset_records = formatted_records
    )
        
    return {
        'dataset': general_dataset,
        'id': dataset_id
    }

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


