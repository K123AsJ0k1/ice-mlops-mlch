
def workflow_handle_internal_datasets(
    swift_client: any,
    internal_material_parameters: str
):
    try:
        import os
        import re
        import time as t
        from ..parser.use import parser_process_material
        from ..workflow.utility import workflow_store_data
        from pathlib import Path
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)

    start_time = t.time()

    internal_material_path = Path(internal_material_parameters['material-path'])
    internal_material_prefix = internal_material_parameters['material-prefix']
    internal_material_exluded_directories = internal_material_parameters['excluded-material']
    internal_material_file_types = internal_material_parameters['file-types']
    internal_material_excluded_folders = internal_material_parameters['excluded-folders']
    internal_material_repository_name = internal_material_parameters['repository-name']
    internal_material_storage_folder = internal_material_parameters['storage-folder']
    internal_material_header_start = internal_material_parameters['header-start']
    internal_material_data_prefix = internal_material_parameters['data-prefix']
    internal_material_storage_parameters = internal_material_parameters['storage-parameters']
    
    def natural_sort_key(path):
        s = str(path)
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

    matching_directories = []
    for directory in internal_material_path.iterdir():
        target_directory = str(directory)
        directory_name = target_directory.split('/')[-1]
        if internal_material_prefix in directory_name:
            if not directory_name in internal_material_exluded_directories:
                matching_directories.append(str(target_directory))

    sorted_directories = sorted(matching_directories, key = natural_sort_key)
    
    for directory in sorted_directories:
        storage_name = directory.split('/')[-1]
        material = parser_process_material(
            directory = directory,
            file_types = internal_material_file_types,
            exclude_folders = internal_material_excluded_folders,
            repository_name = internal_material_repository_name,
            save_material = True,
            storage_folder = internal_material_storage_folder,
            storage_name = storage_name,
            header_start = internal_material_header_start,
            debug_prints = False
        )
        
    internal_storage_time = workflow_store_data(
        swift_client = swift_client,
        storage_parameters = internal_material_storage_parameters,
        data_prefix = internal_material_data_prefix,
        data_source = internal_material_storage_folder,
        data_type = 'internal'
    )

    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print(f'Spent seconds: {total_time}')

    return total_time

def workflow_format_internal_datasets(
    swift_client: any,
    storage_parameters: any,
    dataset_paths: list,
    ref_column: str,
    path_column: str,
    material_grades: dict,
    insert_prefix: str,
    format_prefix: str,
    group_columns: list,
    value_column: str,
    weigth_column: str
):
    try: 
        import time as t
        import pandas as pd
        from ..objects.use import objects_get_data, objects_store_data
        from ..workflow.utility import workflow_set_weights, workflow_grade_row
    except ImportError as e:
        raise ImportError("workflow/use failed to import", e)

    start_time = t.time()

    checked_datasets = [] 
    idx = 0
    global_ref_paths = {}
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

        df_records = data_object[0].to_dict('records')
        dataset_rows_1 = []
        for row in df_records:
            formatted_row = row.copy()
            formatted_row['idx'] = idx
            formatted_row['dataset-object'] = dataset_path
            global_ref_paths.update(formatted_row[ref_column])
            dataset_rows_1.append(formatted_row)
            idx += 1
        checked_datasets.append(dataset_rows_1)

    dataset_idx = 0
    for dataset_path in dataset_paths:
        dataset_rows_2 = []
        
        for row in checked_datasets[dataset_idx]:
            formatted_row = row.copy()
            formatted_row['relevance'] = workflow_grade_row(
                data_row = row,
                path_column = path_column,
                global_reference_paths = global_ref_paths,
                material_grades = material_grades
            )

            dataset_rows_2.append(formatted_row)
        
        before, match, after = dataset_path.partition(insert_prefix)
        modified_dataset_path = f'{before}{match}-{format_prefix}{after}'
        dataset_df = pd.DataFrame(dataset_rows_2)
        dataset_df['ranking-weights'] = workflow_set_weights(
            target_df = dataset_df,
            group_columns = group_columns,
            value_column = value_column,
            weight_column = weigth_column
        )

        status = objects_store_data(
            swift_client = swift_client,
            storage_parameters = {
                'bucket-target': storage_parameters['bucket-target'],
                'bucket-prefix': storage_parameters['bucket-prefix'],
                'bucket-user': storage_parameters['bucket-user'],
                'object-name': 'root',
                'object-serialization': storage_parameters['object-serialization'],
                'path-replacers': {
                    'name': modified_dataset_path
                },
                'path-names': [],
                'debug-prints': True,
                'lock-parameters': {},
                'lock-location': None,
                'overwrite': True
            },
            object_data = dataset_df,
            object_metadata = {}
        )
        dataset_idx += 1

    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print(f'Spent seconds: {total_time}')

    return total_time

def workflow_handle_external_datasets(
    swift_client: any,
    external_material_parameters: any
):
    try:
        import os
        import re
        import time as t
        from pathlib import Path
        import pandas as pd
        from ..workflow.utility import workflow_divide_external_data
        from ..workflow.utility import workflow_store_data
        from datasets import load_dataset
    except ImportError as e:
        raise ImportError("workflow/use failed to import", e)

    start_time = t.time()
    
    external_material_hf_token = external_material_parameters['hf-token']
    external_material_storage_folder = external_material_parameters['storage-folder']
    external_material_dataset_details = external_material_parameters['dataset-details']
    external_material_data_prefix = external_material_parameters['data-prefix']
    external_material_storage_parameters = external_material_parameters['storage-parameters']
    
    for details in external_material_dataset_details:
        processing_type = details['processing-type']
        dataset_repository = details['dataset-repository']
        dataset_name = details['dataset-name']
        if processing_type == 'full':
            dataset_path = f'{external_material_storage_folder}/{details['file-name']}.parquet'
            absolute_file_path = Path(dataset_path).resolve()
            
            if not absolute_file_path.exists():
                dataset = load_dataset(
                    dataset_repository, 
                    dataset_name,
                    streaming = False,
                    token = external_material_hf_token
                )

                dataset_df = None
                if 'humaneval' in dataset_repository:
                    dataset_df = dataset['test'].to_pandas().filter(['prompt','canonical_solution']).rename(columns = {
                        'prompt': 'question',
                        'canonical_solution': 'answer'
                    })

                if 'mbpp' in dataset_repository:
                    dataset_df = pd.concat([
                        dataset['train'].to_pandas(),
                        dataset['test'].to_pandas(), 
                        dataset['validation'].to_pandas(), 
                        dataset['prompt'].to_pandas()
                    ])
                    dataset_df = dataset_df.filter(['prompt','code']).rename(columns = {
                        'prompt': 'question',
                        'code': 'answer'
                    })

                if 'bash' in dataset_repository:
                    dataset_df = dataset['train'].to_pandas().rename(columns = {
                        'prompt': 'question',
                        'completion': 'answer'
                    })

                if not dataset_df is None:
                    print(f'Storing dataset into {dataset_path}')
                    dataset_df.to_parquet(absolute_file_path, engine = 'pyarrow')
    
        if processing_type == 'divided':
            table_size = details['table-size']
            size_limit = details['size-limit']
            data_name = f'{dataset_repository.split('/')[-1]}-{dataset_name}'
            data_name = data_name.replace('_', '-')
            
            folder_path = Path(f'./{external_material_storage_folder}')
            files = [f.name for f in folder_path.iterdir() if f.is_file()]
            prefix_exists = any(file.startswith(data_name) for file in files)
            path_prefix = f'{external_material_storage_folder}/{data_name}'
            
            if not prefix_exists:
                total_time = workflow_divide_external_data(
                    dataset_repository = dataset_repository,
                    dataset_name = dataset_name,
                    hf_token = external_material_hf_token,
                    table_size = table_size,
                    size_limit = size_limit,
                    relevant_columns = [
                        'instruction',
                        'output'
                    ],
                    renamed_columns = {
                        'instruction': 'question',
                        'output': 'answer'
                    },
                    path_prefix = path_prefix
                )

    internal_storage_time = workflow_store_data(
        swift_client = swift_client,
        storage_parameters = external_material_storage_parameters,
        data_prefix = external_material_data_prefix,
        data_source = external_material_storage_folder,
        data_type = 'external'
    )

    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print(f'Spent seconds: {total_time}')

    return total_time

