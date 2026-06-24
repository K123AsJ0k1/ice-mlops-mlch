
def rag_setup_database(
    swift_client: any,
    qdrant_client: any,
    storage_parameters: any,
    collection_name: str,
    dataset_paths: list,
    text_column: str,
    text_encoder: any
) -> any:
    try:
        from ..objects.use import objects_get_data
        from ..qdrant.use import qdrant_create_collection, qdrant_hybrid_config, qdrant_upload_points
        from ..embeddings.use import embeddings_create_hybrid_points
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)
    
    status = qdrant_create_collection(
        qdrant_client = qdrant_client, 
        collection_name = collection_name,
        configuration = qdrant_hybrid_config()
    )

    global_vocabulary = {}
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

        hybrid_points, global_vocabulary = embeddings_create_hybrid_points(
            dataset_name = dataset_name,
            target_df = target_df,
            text_column = text_column,
            text_encoder = text_encoder,
            global_vocabulary = global_vocabulary
        )
        # Maybe check if the points already exist
        status = qdrant_upload_points(
            qdrant_client = qdrant_client, 
            collection_name = collection_name,
            points = hybrid_points
        ) 
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
    text_encoder: any,
    debug_prints: bool
):
    try:
        from ..objects.use import objects_get_data
        from ..search.use import search_data_metrics
        from ..search.utility import search_get_statistics
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)

    dataset_stat_list = []
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

        target_df = data_object[0].rename_axis('idx').reset_index()

        dataframe_stats, collective_metrics = search_data_metrics(
            target_df = target_df,
            group_columns = group_columns,
            value_column = value_column,
            query_column = query_column,
            qdrant_client = qdrant_client,
            query_type = query_type,
            collection_name = collection_name,
            query_limit = query_limit,
            fusion_limit = fusion_limit,
            text_encoder = text_encoder,
            global_vocabulary = {},
            debug_prints = debug_prints,
            gathered_metrics = collective_metrics
        )
        
        dataset_stat_list.append(dataframe_stats)
    
    complete_summary = search_get_statistics(
        gathered_metrics = collective_metrics,
        percentile_filter = [
            'p@1',
            'r@3',
            'ndcg@3',
            'ndcg@5'
        ]
    )

    return complete_summary, dataset_stat_list