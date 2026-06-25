def search_get_batch_vectors(
    query_type: str,
    text_query_batch: list,
    dense_model: any,
    sparse_model: any
):
    try:
        from qdrant_client import models
        from ..sparse.use import sparse_create_spalde_embeddings
        from ..dense.use import dense_create_baai_vectors
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)
    
    queries_dense = []
    is_dense_needed = query_type in ('dense', 'hybrid-rrf', 'hybrid-dbsf')
    is_sparse_needed = query_type in ('sparse', 'hybrid-rrf', 'hybrid-dbsf')

    if is_dense_needed and dense_model is not None:
        queries_dense = dense_create_baai_vectors(
            dense_model = dense_model,
            text_inputs = text_query_batch
        )

    queries_sparse = []
    if is_sparse_needed and sparse_model is not None:
        sparse_embeddings_iter = sparse_create_spalde_embeddings(
            sparse_model = sparse_model,
            text_inputs = text_query_batch
        )
        
        queries_sparse = [
            models.SparseVector(
                indices=emb.indices.tolist(),
                values=emb.values.tolist()
            )
            for emb in sparse_embeddings_iter
        ]

    return queries_dense, queries_sparse

def search_monitored_batch_query(
    qdrant_client: any,
    query_type: str,
    collection_name: str,
    text_query_batch: list, 
    relevant_ids_batch: list,
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
    batch_dense, batch_sparse = search_get_batch_vectors(
        query_type = query_type,
        text_query_batch = text_query_batch,
        dense_model = dense_model,
        sparse_model = sparse_model
    )
    embed_latency_ms = ((time.perf_counter_ns() - start_embed) / 1e6) / len(text_query_batch)
    batch_results = []

    # 2. Query Qdrant
    for idx, query_text in enumerate(text_query_batch):
        q_dense = []
        if 0 < len(batch_dense):
            q_dense = batch_dense[idx] if batch_dense is not None else None
        q_sparse = []
        if 0 < len(batch_sparse):
            q_sparse = batch_sparse[idx] if batch_sparse is not None else None
        q_relevant_ids = []
        if 0 < len(relevant_ids_batch):
            q_relevant_ids = relevant_ids_batch[idx]

        start_search = time.perf_counter_ns()
        query_result = qdrant_modifiable_query( 
            qdrant_client = qdrant_client, 
            query_type = query_type,
            collection_name = collection_name,
            query_dense = q_dense,
            query_sparse = q_sparse,
            query_limit = query_limit,
            fusion_limit = fusion_limit
        )
        search_latency_ms = (time.perf_counter_ns() - start_search) / 1e6
        
        total_characters = sum(point.payload.get('characters', 0) for point in query_result)
        retrieved_ids = [point.payload['idx'] for point in query_result]
        
        resulted_metrics = {}
        if 0 < len(q_relevant_ids):
            resulted_metrics = search_retrieval_metrics( 
                retrieved_ids = retrieved_ids,
                true_relevant_ids = q_relevant_ids
            )
        
        resulted_metrics['embedding-latency-ms'] = embed_latency_ms
        resulted_metrics['search-latency-ms'] = search_latency_ms
        resulted_metrics['total-latency-ms'] = embed_latency_ms + search_latency_ms
        resulted_metrics['total-characters'] = total_characters

        batch_results.append((query_result, resulted_metrics))

    return batch_results

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
    debug_prints: bool
):
    try:
        from ..search.utility import search_get_statistics
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)

    relevance_lookup = target_df.groupby(group_columns)[value_column].apply(list).to_dict()
    
    text_queries = []
    relevant_ids_batch = []
    metadata_rows = [] 

    for _, row in target_df.iterrows():
        group_key = tuple(row[column] for column in group_columns)
        text_queries.append(row[query_column])
        relevant_ids_batch.append(relevance_lookup[group_key])
        metadata_rows.append(row)
    
    batch_outputs = search_monitored_batch_query(
        qdrant_client = qdrant_client,
        query_type = query_type,
        collection_name = collection_name,
        text_query_batch = text_queries, 
        relevant_ids_batch = relevant_ids_batch, 
        query_limit = query_limit,
        fusion_limit = fusion_limit,
        dense_model = dense_model,
        sparse_model = sparse_model
    )
    
    # 3. Unpack batch results for debugging and metric aggregation
    gathered_metrics = {}
    for j, (result, metrics) in enumerate(batch_outputs):
        row = metadata_rows[j]
        query_text = text_queries[j]
        true_relevant_ids = relevant_ids_batch[j]

        if debug_prints:
            print(f'Dataset|{dataset_name}')
            print(f'Collection|{collection_name}')
            print(f'Case|{j+1}')
            print(f'Query|{query_text}')
            print(f'Query type|{query_type}')

            if query_type == 'dense' or 'hybrid' in query_type:
                print(f'Dense model: {dense_model_name}')
            if query_type == 'sparse' or 'hybrid' in query_type:
                print(f'Sparse model: {sparse_model_name}')
            
            print(f'Relevant ids|{true_relevant_ids}')
            print(f"Precision@1|{metrics['p@1']}")
            print(f"Recall@3|{metrics['r@3']}")
            print(f"NDCG@3|{metrics['ndcg@3']}")
            print(f"NDCG@5|{metrics['ndcg@5']}")
            print(f"Embedding latency (ms)|{metrics['embedding-latency-ms']}")
            print(f"Search latency (ms)|{metrics['search-latency-ms']}")
            print(f"Total latency (ms)|{metrics['total-latency-ms']}")
            print(f"Total retrieved characters|{metrics['total-characters']}")
            print('index|score|idx|part|document|chapter|index|topic')
            for i, point in enumerate(result, 1):
                p = point.payload
                print(f"{i}|{point.score}|{p.get('idx')}|{p.get('part')}|{p.get('document')}|{p.get('chapter')}|{p.get('index')}|{p.get('topic')}")
            print('')

        for key, value in metrics.items():
            if key not in gathered_metrics:
                gathered_metrics[key] = []
            gathered_metrics[key].append(value)
    # Potential source
    print(gathered_metrics)
    dataframe_statistics = search_get_statistics(
        gathered_metrics = gathered_metrics,
        percentile_filter = ['p@1', 'r@3', 'ndcg@3', 'ndcg@5']
    )
    
    return dataframe_statistics, gathered_metrics