import ray
import time as t

from icebreaker.swift.setup import swift_setup_client
from icebreaker.objects.use import objects_get_data
from icebreaker.qdrant.setup import qdrant_setup_client
from icebreaker.qdrant.use import qdrant_create_point, qdrant_upload_points
from icebreaker.embeddings.utility import embeddings_generate_uuid
from icebreaker.rag.utility import rag_format_data

@ray.remote(
    num_cpus = 1,
    memory = 0.2 * 1024 * 1024 * 1024
) 
def database_setup(
    worker_index: int,
    actor_index: int,
    actor_ref: any,
    swift_parameters: dict,
    qdrant_parameters: dict,
    collection_name: str,
    input_storage_parameters: dict,
    output_storage_parameters: dict,
    config_parameters: dict,
    process_parameters: dict,
    task_batch: list
) -> dict: 
    start_time = t.time()
    print(f'Task {worker_index}, Actor {actor_index}')
    
    work_swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )
    print('Swift client setup') 

    work_qdrant_client = qdrant_setup_client(
        qdrant_parameters = qdrant_parameters
    )

    text_column = config_parameters['text-column']
    process_batch_size = config_parameters['batch-size']
    generator_actor_refs = []
    dataset_records_map = {}
    stored_dfs = {}
    for data_index, batch_data in enumerate(task_batch):
        object_path = batch_data[0]
        
        data_object = objects_get_data(
            swift_client = work_swift_client,
            storage_parameters = {
                'bucket-target': input_storage_parameters['bucket-target'],
                'bucket-prefix': input_storage_parameters['bucket-prefix'],
                'bucket-user': input_storage_parameters['bucket-user'],
                'object-name': 'root',
                'object-serialization': input_storage_parameters['object-serialization'],
                'path-replacers': {
                    'name': object_path
                },
                'path-names': [],
                'debug-prints': True,
                'lock-parameters': {},
                'lock-location': None,
                'overwrite': True
            },
            dict_format = False 
        )  
        
        pandas_df = data_object[0]
        df_records = pandas_df.to_dict('records')
        dataset_records_map[data_index] = df_records

        key_name = object_path.split('/')[-1].split('.')[0]

        stored_dfs[key_name] = pandas_df
 
        total_rows = len(pandas_df)
        calclated_chunk = int(total_rows * 0.05)
        chunk_size = max(1, calclated_chunk)
        for i in range(0, total_rows, chunk_size):
            df_chunk = pandas_df.iloc[i : i + chunk_size]
            text_chunk = df_chunk[text_column].tolist()
            # Retain absolute index tracking within this individual file
            chunk_row_indices = list(range(i, i + len(df_chunk)))
            
            text_input_ref = ray.put(text_chunk)
            generator_actor_refs.append(actor_ref.batch_generate_vectors.remote(
                worker_index = worker_index, 
                actor_index = actor_index, 
                data_index = data_index,
                batch_index = i,
                key_name = key_name, 
                text_input_batch = text_input_ref,
                batch_size = process_batch_size,
                row_indices = chunk_row_indices
            ))

    hybrid_points = []
    formatted_metrics = {}
    while len(generator_actor_refs) > 0:
        done_refs, generator_actor_refs = ray.wait(generator_actor_refs)
        for output_ref in done_refs: 
            batch = ray.get(output_ref)

            batch_index = batch['batch_idx']            
            batch_dataset_index = batch['data_idx']
            batch_key_name = batch['key_name']
            row_indices = batch['row_indices']
            dense_result = batch['dense']
            dense_vectors = dense_result['data']
            dense_time = dense_result['mean-time-ms']
            sparse_result = batch['sparse']
            sparse_time = sparse_result['mean-time-ms']
            sparse_vectors = sparse_result['data']

            dense_stat_key = f'dense-batch-{batch_index}-mean-time-ms'
            sparse_stat_key = f'sparse-batch-{batch_index}-mean-time-ms'
            
            formatted_metrics[batch_key_name] = {
                dense_stat_key: dense_time,
                sparse_stat_key: sparse_time
            }
            
            source_records = dataset_records_map[batch_dataset_index]

            for idx_in_chunk, actual_row_idx in enumerate(row_indices):
                d_vec = dense_vectors[idx_in_chunk] if dense_vectors is not None else None
                s_vec = sparse_vectors[idx_in_chunk] if sparse_vectors is not None else None
                
                # Fetch exact correct row payload matching this vector
                dataset_row = source_records[actual_row_idx]

                # Fixed index alignment bugs via actual_row_idx
                point_uuid = embeddings_generate_uuid(
                    id = key_name,
                    index = actual_row_idx
                )

                created_point = qdrant_create_point(
                    point_uuid = point_uuid,
                    point_dense_vector = {"dense": d_vec} if d_vec else None,
                    point_sparse_vector = {"sparse": s_vec} if s_vec else None,
                    point_payload = dataset_row
                )
                hybrid_points.append(created_point)
    
    status = qdrant_upload_points(
        qdrant_client = work_qdrant_client, 
        collection_name = collection_name,
        points = hybrid_points
    ) 
    query_column = config_parameters['query-column']
    weight_column = config_parameters['weight-column']
    query_type = config_parameters['query-type']
    relevance_threshold = config_parameters['relevance-threshold']
    query_limit = config_parameters['query-limit']
    fusion_limit = config_parameters['fusion-limit']
    generator_actor_refs = []
    for dataset_name, df in stored_dfs.items():
        df_text_queries = df[query_column].tolist()
        df_relevant_weights = df[weight_column].tolist()

        text_query_ref = ray.put(df_text_queries)
        relevant_weight_ref = ray.put(df_relevant_weights)
        generator_actor_refs.append(actor_ref.batch_generate_vectors.remote(
            key_name = dataset_name,
            query_type = query_type,
            collection_name = collection_name,
            text_query_batch = text_query_ref,
            relevant_weights_batch = relevant_weight_ref,
            relevance_threshold = relevance_threshold,
            query_limit = query_limit,
            fusion_limit = fusion_limit,
            batch_size = process_batch_size
        ))

    retrieval_outputs = {
        'parameters': {
            'type': query_type,
            'query-limit': query_limit,
            'fusion-limit': fusion_limit,
            'relevance-threshold': relevance_threshold,
            'batch-size': process_batch_size
        },
        'tables': {}
    }

    results = []
    while len(generator_actor_refs) > 0:
        done_refs, generator_actor_refs = ray.wait(generator_actor_refs)
        for output_ref in done_refs: 
            batch = ray.get(output_ref)

            key_name = batch['key_name']

            retrieval_outputs['tables'][key_name] = batch
            
            
            #query_results = batch['results']
            #query_metrics = batch['metrics']
            #key_name = batch['key_name']
            #dense_time = batch['dense-mean-time-ms']
            #sparse_time = batch['sparse-mean-time-ms']

            #dense_stat_key = f'dense-query-{batch_index}-mean-time-ms'
            #sparse_stat_key = f'sparse-query-{batch_index}-mean-time-ms'

            #formatted_metrics[batch_key_name] = {
            #    dense_stat_key: dense_time,
            #    sparse_stat_key: sparse_time
            #}

            #retrieval_outputs['tables'][key_name] = dataset_output

    formatted_rag_data = rag_format_data(
        retrieval_outputs = retrieval_outputs,
        metric_columns = [
            'p@1',
            'r@3',
            'rr',
            'ap',
            'ndcg@3',
            'ndcg@5',
            'embedding-latency-ms',
            'search-latency-ms',
            'total-latency-ms',
            'total-characters'
        ]
    )

    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return formatted_rag_data