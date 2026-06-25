def search_get_vectors(
    query_type: str,
    query_text: str,
    dense_model: any,
    sparse_model: any
):
    try:
        from qdrant_client import models
        from ..sparse.use import sparse_create_spalde_tuple
        from ..dense.use import dense_create_baai_vector
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)
    query_dense = None
    if query_type == 'dense' or query_type == 'hybrid-rrf' or query_type == 'hybrid-dbsf':
        query_dense = dense_create_baai_vector(
            dense_model = dense_model,
            vector_text = query_text
        )
    query_sparse = None
    if query_type == 'sparse' or query_type == 'hybrid-rrf' or query_type == 'hybrid-dbsf':
        indices, values = sparse_create_spalde_tuple(
            sparse_model = sparse_model,
            vector_text = query_text
        )
        query_sparse = models.SparseVector(indices=indices, values=values)
    return query_dense, query_sparse

def search_monitored_query(
    qdrant_client: any,
    query_type: str,
    collection_name: str,
    query_text: str, 
    relevant_ids: list,
    query_limit: int,
    fusion_limit: int,
    dense_model: any,
    sparse_model: any
) -> any:
    try:
        import time
        from ..qdrant.use import qdrant_modifiable_query
        from ..search.utility import search_retrieval_metrics
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)
    
    start_embed = time.perf_counter_ns()
    query_dense, query_sparse = search_get_vectors(
        query_type = query_type,
        query_text = query_text,
        dense_model = dense_model,
        sparse_model = sparse_model
    )
    embed_latency_ms = (time.perf_counter_ns() - start_embed) / 1e6
    
    start_search = time.perf_counter_ns()
    query_result = qdrant_modifiable_query(
        qdrant_client = qdrant_client, 
        query_type = query_type,
        collection_name = collection_name,
        query_dense = query_dense,
        query_sparse = query_sparse,
        query_limit = query_limit,
        fusion_limit = fusion_limit
    )
    search_latency_ms = (time.perf_counter_ns() - start_search) / 1e6
    
    total_retrieval_ms = embed_latency_ms + search_latency_ms
    total_characters = 0
    for point in query_result:
        total_characters += point.payload['characters']
    
    retrieved_ids = []
    for point in query_result:
        point_idx = point.payload['idx']
        retrieved_ids.append(point_idx)
    
    resulted_metrics = search_retrieval_metrics(
        retrieved_ids = retrieved_ids,
        true_relevant_ids = relevant_ids
    )
    
    resulted_metrics['embedding-latency-ms'] = embed_latency_ms
    resulted_metrics['search-latency-ms'] = search_latency_ms
    resulted_metrics['total-latency-ms'] = total_retrieval_ms
    resulted_metrics['total-characters'] = total_characters

    return query_result, resulted_metrics

def search_data_metrics(
    dataset_name: str,
    target_df: any,
    group_columns: list,
    value_column: str,
    query_column: str,
    qdrant_client: any,
    query_type: str,
    collection_name: str,
    query_limit: int,
    fusion_limit: int,
    dense_model_name: str,
    dense_model: any,
    sparse_model_name: str,
    sparse_model: any,
    gathered_metrics: dict,
    debug_prints: bool
):
    try:
        from ..search.utility import search_get_statistics
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)

    dataset_metrics = {}
    relevance_lookup = target_df.groupby(group_columns)[value_column].apply(list).to_dict()
    for j, row in target_df.iterrows():
        group_key = ()
        for column in group_columns:
            group_key = group_key + (row[column],)

        true_relevant_ids = relevance_lookup[group_key]
        query_text = row[query_column]
        
        result, metrics = search_monitored_query(
            qdrant_client = qdrant_client,
            query_type = query_type,
            collection_name = collection_name,
            query_text = query_text, 
            relevant_ids = true_relevant_ids,
            query_limit = query_limit,
            fusion_limit = fusion_limit,
            dense_model = dense_model,
            sparse_model = sparse_model
        )

        if debug_prints:
            print(f'Dataset|{dataset_name}')
            print(f'Collection|{collection_name}')
            print(f'Case|{j+1}')
            print(f'Query|{query_text}')
            print(f'Query type|{query_type}')

            if query_type == 'dense' or 'hybrid' in query_type:
                print(f'Dense model: {dense_model_name}')
            if query_type == 'sparse'  or 'hybrid' in query_type:
                print(f'Sparse model: {sparse_model_name}')
            
            print(f'Relevant ids|{true_relevant_ids}')
            print(f'Precision@1|{metrics['p@1']}')
            print(f'Recall@3|{metrics['r@3']}')
            print(f'NDCG@3|{metrics['ndcg@3']}')
            print(f'NDCG@5|{metrics['ndcg@5']}')
            print(f'Embedding latency (ms)|{metrics['embedding-latency-ms']}')
            print(f'Search latency (ms)|{metrics['search-latency-ms']}')
            print(f'Total latency (ms)|{metrics[ 'total-latency-ms']}')
            print(f'Total retrieved characters|{metrics['total-characters']}')
            print('index|score|idx|part|document|chapter|index|topic')
            for i, point in enumerate(result, 1):
                print(f'{i}|{point.score}|{point.payload['idx']}|{point.payload['part']}|{point.payload['document']}|{point.payload['chapter']}|{point.payload['index']}|{point.payload['topic']}')
            print('')

        for key, value in metrics.items():
            if not key in gathered_metrics:
                gathered_metrics[key] = []
            if not key in dataset_metrics:
                dataset_metrics[key] = []
            gathered_metrics[key].append(value)
            dataset_metrics[key].append(value)

    dataframe_statistics = search_get_statistics(
        gathered_metrics = dataset_metrics,
        percentile_filter = [
            'p@1',
            'r@3',
            'ndcg@3',
            'ndcg@5'
        ]
    )
    
    return dataframe_statistics, gathered_metrics