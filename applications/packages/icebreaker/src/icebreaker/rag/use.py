
def rag_setup_database(
    swift_client: any,
    qdrant_client: any,
    storage_parameters: any,
    collection_name: str,
    dataset_paths: list,
    text_column: str,
    dense_model: any,
    sparse_model: any,
    batch_size: int
) -> any:  
    try: 
        import time as t
        from ..objects.use import objects_get_data
        from ..qdrant.use import qdrant_create_collection, qdrant_upload_points
        from ..qdrant.utility import qdrant_hybrid_config
        from ..embeddings.use import embeddings_create_hybrid_points
    except ImportError as e:
        raise ImportError("rag/use failed to import", e)
    
    start_time = t.time()

    print(f'Creating collection: {collection_name}')
    status = qdrant_create_collection(
        qdrant_client = qdrant_client, 
        collection_name = collection_name,
        configuration = qdrant_hybrid_config()
    )

    dense_times = {}
    sparse_times = {}
    total_times = {}
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

        dataset_name = dataset_path.split('/')[-1].split('.')[0]
        df_records = data_object[0].to_dict('records')

        total_batch_start_time = t.time()
        results = embeddings_create_hybrid_points(
            dataset_name = dataset_name,
            dataset_records = df_records,
            text_column = text_column,
            dense_model = dense_model,
            sparse_model = sparse_model,
            batch_size = batch_size
        )
        total_batch_end_time = t.time()

        # Maybe check if the points already exist
        status = qdrant_upload_points(
            qdrant_client = qdrant_client, 
            collection_name = collection_name,
            points = results['points']
        ) 

        dense_times[dataset_name] = results['dense-time']
        sparse_times[dataset_name] = results['sparse-time']
        total_times[dataset_name] = total_batch_end_time - total_batch_start_time

    end_time = t.time()

    setup_time = round(end_time-start_time,5)

    return {
        'dense-times': dense_times,
        'sparse-times': sparse_times,
        'total-times': total_times,
        'setup-time': setup_time
    }
  
def rag_evalute_database(
    swift_client: any,
    qdrant_client: any,
    storage_parameters: any,
    collection_name: str,
    query_type: str,
    query_limit: int,
    group_columns: list,
    value_column: str,
    relevance_column: str,
    query_column: str,
    fusion_limit: int,
    dataset_paths: list,
    dense_model: any,
    dense_model_name: str,
    sparse_model: any,
    sparse_model_name: str,
    batch_size: int, 
    debug_prints: bool
):
    try:
        from ..objects.use import objects_get_data
        from ..search.use import search_data_metrics
        from ..search.utility import search_get_statistics
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)

    database_metrics = {}
    database_metrics['query-type'] = query_type
    if query_type == 'dense' or 'hybrid' in query_type:
        database_metrics['dense-model'] = dense_model_name
    if query_type == 'sparse'  or 'hybrid' in query_type:
        database_metrics['sparse-model'] = sparse_model_name
    
    global_collective_metrics = {}
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
        dataset_name = dataset_path.split('/')[-1].split('.')[0]
        target_df = data_object[0]
         
        dataframe_stats, current_dataset_gather = search_data_metrics(
            dataset_name = dataset_name, 
            target_df = target_df,
            group_columns = group_columns,
            value_column = value_column,
            relevance_column = relevance_column,
            query_column = query_column,
            qdrant_client = qdrant_client,
            query_type = query_type,
            collection_name = collection_name,
            query_limit = query_limit,
            fusion_limit = fusion_limit,
            dense_model_name = dense_model_name,
            dense_model = dense_model,
            sparse_model_name = sparse_model_name,
            sparse_model = sparse_model,
            batch_size = batch_size,
            debug_prints = debug_prints
        ) 

        database_metrics[dataset_name] = dataframe_stats
        for key, values in current_dataset_gather.items():
            if key not in global_collective_metrics:
                global_collective_metrics[key] = []
            global_collective_metrics[key].extend(values)
    
    database_metrics['summary'] = search_get_statistics(
        gathered_metrics = global_collective_metrics,
        percentile_filter = [
            'p@1-proxy',
            'r@3-proxy',
            'ndcg@3-graded',
            'ndcg@5-graded'
        ]
    )

    return database_metrics