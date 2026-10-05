
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

        total_batch_start_time = t.perf_counter_ns()
        results = embeddings_create_hybrid_points(
            dataset_name = dataset_name,
            dataset_records = df_records,
            text_column = text_column,
            dense_model = dense_model,
            sparse_model = sparse_model,
            batch_size = batch_size
        )
    
        dense_times[dataset_name] = results['dense-mean-time-ms']
        sparse_times[dataset_name] = results['sparse-mean-time-ms']
        
        total_times[dataset_name] = ((t.perf_counter_ns() - total_batch_start_time) / 1e6) / len(df_records)

        # Maybe check if the points already exist
        status = qdrant_upload_points(
            qdrant_client = qdrant_client, 
            collection_name = collection_name,
            points = results['points']
        ) 

    end_time = t.time()

    setup_time = round(end_time-start_time,5)
    
    return {
        'dense-times-ms': dense_times,
        'sparse-times-ms': sparse_times,
        'total-times-ms': total_times,
        'setup-time-sec': setup_time
    }

def rag_evalute_retrieval(
    swift_client: any,
    qdrant_client: any,
    storage_parameters: any,
    collection_name: str,
    relevance_threshold: float,
    query_type: str,
    query_limit: int,
    query_column: str,
    weight_column: str,
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
        from ..rag.utility import rag_data_metrics
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)

    #database_metrics = {}
    collective_metrics = {}
    collective_metrics['query-type'] = query_type
    if query_type == 'dense' or 'hybrid' in query_type:
        collective_metrics['dense-model'] = dense_model_name
    if query_type == 'sparse'  or 'hybrid' in query_type:
        collective_metrics['sparse-model'] = sparse_model_name
    
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
         
        gathered_dataset_metrics = rag_data_metrics(
            dataset_name = dataset_name, 
            target_df = target_df,
            query_column = query_column,
            weigth_column = weight_column,
            qdrant_client = qdrant_client,
            query_type = query_type,
            collection_name = collection_name,
            relevance_threshold = relevance_threshold,
            query_limit = query_limit,
            fusion_limit = fusion_limit,
            dense_model_name = dense_model_name,
            dense_model = dense_model,
            sparse_model_name = sparse_model_name,
            sparse_model = sparse_model,
            batch_size = batch_size,
            debug_prints = debug_prints
        ) 

        #database_metrics[dataset_name] = dataframe_stats
        dataset_metrics = {}
        for key, values in gathered_dataset_metrics.items():
            if key not in dataset_metrics:
                dataset_metrics[key] = []
            dataset_metrics[key].extend(values)
        collective_metrics[dataset_name] = dataset_metrics
    
    #database_metrics['summary'] = rag_get_statistics(
    #    gathered_metrics = global_collective_metrics,
    #    percentile_filter = [
    #        'p@1',
    #        'r@3',
    #        'rr',
    #        'ap',
    #        'ndcg@3',
    #        'ndcg@5'
    #    ]
    #)

    return collective_metrics