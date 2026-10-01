def preprocess_grade_row(
    data_row: any,
    path_column: str,
    global_reference_paths: dict,
    material_grades: dict,
    blacklist_prefixes: list
):
    row_absolute_path = data_row[path_column]
    file_type = row_absolute_path.split('.')[-1]

    row_grade = None
    if file_type in material_grades:
        m_type, row_grade = material_grades[file_type]
        if m_type == 'secondary':
            for blacklist_prefix in blacklist_prefixes:
                if blacklist_prefix in row_absolute_path:
                    # Grade penaly of 0 can be added here
                    break

            for _, absolute_path in global_reference_paths.items():
                if absolute_path == row_absolute_path:
                    row_grade += 1
                    break  
    return row_grade

def preprocess_set_weights(
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

def preprocess_format_datasets(
    swift_client: any,
    storage_parameters: any,
    dataset_paths: list,
    ref_column: str,
    path_column: str,
    material_grades: dict,
    blacklist_prefixes: dict,
    insert_prefix: str,
    format_prefix: str,
    group_columns: list,
    value_column: str,
    weigth_column: str
):
    try: 
        import pandas as pd
        from ..objects.use import objects_get_data, objects_store_data
    except ImportError as e:
        raise ImportError("rag/use failed to import", e)

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
            preprocessed_row = row.copy()
            preprocessed_row['idx'] = idx
            preprocessed_row['dataset-object'] = dataset_path
            global_ref_paths.update(preprocessed_row[ref_column])
            dataset_rows_1.append(preprocessed_row)
            idx += 1
        checked_datasets.append(dataset_rows_1)

    preprocessed_datasets = []
    dataset_idx = 0
    for dataset_path in dataset_paths:
        dataset_rows_2 = []
        
        for row in checked_datasets[dataset_idx]:
            preprocessed_row = row.copy()
            preprocessed_row['relevance'] = preprocess_grade_row(
                data_row = row,
                path_column = path_column,
                global_reference_paths = global_ref_paths,
                material_grades = material_grades,
                blacklist_prefixes = blacklist_prefixes
            )

            dataset_rows_2.append(preprocessed_row)
        
        before, match, after = dataset_path.partition(insert_prefix)
        modified_dataset_path = f'{before}{match}-{format_prefix}{after}'
        dataset_df = pd.DataFrame(dataset_rows_2)
        dataset_df['ranking-weights'] = preprocess_set_weights(
            target_df = dataset_df,
            group_columns = group_columns,
            value_column = value_column,
            weight_column = weigth_column
        )

        preprocessed_datasets.append(dataset_df)
        
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

    return preprocessed_datasets
