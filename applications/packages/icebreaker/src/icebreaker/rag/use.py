
def rag_setup_database(
    swift_client: any,
    qdrant_client: any,
    storage_parameters: any,
    collection_name: str,
    dataset_paths: list,
    text_column: str,
    dense_model: any,
    sparse_model: any
) -> any:
    try: 
        import time as t
        from ..objects.use import objects_get_data
        from ..qdrant.use import qdrant_create_collection, qdrant_upload_points, qdrant_baai_hybrid_config
        from ..embeddings.use import embeddings_create_hybrid_points
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)
    
    start_time = t.time()

    print(f'Creating collection: {collection_name}')
    status = qdrant_create_collection(
        qdrant_client = qdrant_client, 
        collection_name = collection_name,
        configuration = qdrant_baai_hybrid_config() 
    )

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
        target_df = data_object[0].rename_axis('idx').reset_index()

        hybrid_points = embeddings_create_hybrid_points(
            dataset_name = dataset_name,
            target_df = target_df,
            text_column = text_column,
            dense_model = dense_model,
            sparse_model = sparse_model
        )
        # Maybe check if the points already exist
        status = qdrant_upload_points(
            qdrant_client = qdrant_client, 
            collection_name = collection_name,
            points = hybrid_points
        ) 
    
    end_time = t.time()

    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)

    return status

def rag_evalute_database(
    swift_client: any,
    qdrant_client: any,
    storage_parameters: any,
    collection_name: str,
    query_type: str,
    query_limit: int,
    group_columns: list,
    value_column: str,
    query_column: str,
    fusion_limit: int,
    dataset_paths: list,
    dense_model: any,
    dense_model_name: str,
    sparse_model: any,
    sparse_model_name: str,
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
    
    collective_metrics = {}
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
        target_df = data_object[0].rename_axis('idx').reset_index()

        dataframe_stats, collective_metrics = search_data_metrics(
            dataset_name = dataset_name,
            target_df = target_df,
            group_columns = group_columns,
            value_column = value_column,
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
            gathered_metrics = collective_metrics,
            debug_prints = debug_prints,
        )

        database_metrics[dataset_name] = dataframe_stats
    
    database_metrics['summary'] = search_get_statistics(
        gathered_metrics = collective_metrics,
        percentile_filter = [
            'p@1',
            'r@3',
            'ndcg@3',
            'ndcg@5'
        ]
    )

    return database_metrics