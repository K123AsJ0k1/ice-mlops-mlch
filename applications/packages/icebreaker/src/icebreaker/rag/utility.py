def rag_query_embeddings(
    query_type: str,
    text_query_batch: list,
    dense_model: any,
    sparse_model: any,
    batch_size: int
):
    try:
        import time as t
        import torch
        from qdrant_client import models
        from ..dense.use import dense_create_vectors
        from ..sparse.use import sparse_create_neural_sparse_embeddings
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)
     
    dense_vectors = {
        'data': None,
        'mean-time-ms': 0
    } 
    is_dense_needed = query_type in ('dense', 'hybrid-rrf', 'hybrid-dbsf')
    is_sparse_needed = query_type in ('sparse', 'hybrid-rrf', 'hybrid-dbsf')
    
    if is_dense_needed and dense_model is not None:
        dense_batch_start_time = t.perf_counter_ns()
        dense_vectors['data'] = dense_create_vectors(
            dense_model = dense_model,
            text_inputs = text_query_batch,
            batch_size = batch_size
        )
        dense_vectors['mean-time-ms'] = ((t.perf_counter_ns() - dense_batch_start_time) / 1e6) / len(text_query_batch)

    sparse_vectors = {
        'data': None,
        'mean-time-ms': 0
    }
    if is_sparse_needed and sparse_model is not None:
        sparse_batch_start_time = t.perf_counter_ns()
        sparse_tensors = sparse_create_neural_sparse_embeddings(
            sparse_model = sparse_model,
            text_inputs = text_query_batch,
            batch_size = batch_size
        )
        
        qdrant_vectors = []
        # Loop over each document's 1D sparse tensor row
        for doc_tensor in sparse_tensors:
            # Get non-zero indices (token IDs) and their corresponding non-zero weights
            non_zero_indices = torch.nonzero(doc_tensor).squeeze(-1)
            non_zero_values = doc_tensor[non_zero_indices]
            
            qdrant_vectors.append(
                models.SparseVector(
                    indices = non_zero_indices.tolist(),
                    values = non_zero_values.tolist()
                )
            )
        sparse_vectors['data'] = qdrant_vectors
        sparse_vectors['mean-time-ms'] = ((t.perf_counter_ns() - sparse_batch_start_time) / 1e6) / len(text_query_batch)
    
    return {
        'dense': dense_vectors,
        'sparse': sparse_vectors
    }

def rag_batch_query(
    qdrant_client: any,
    query_type: str,
    collection_name: str,
    text_query_batch: list, 
    relevant_weights_batch: list,
    relevance_threshold: float,
    query_limit: int,
    fusion_limit: int,
    dense_model_name: str,
    dense_model: any,
    sparse_model_name: str,
    sparse_model: any,
    batch_size: int
) -> any:
    try:
        import time
        from ..qdrant.use import qdrant_modifiable_query
        from ..evaluation.use import evalution_ranking_metrics
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)
    
    total_embed_start = time.perf_counter_ns()
    result = rag_query_embeddings(
        query_type = query_type,
        text_query_batch = text_query_batch,
        dense_model = dense_model,
        sparse_model = sparse_model,
        batch_size = batch_size
    )
    total_embed_total_ms = ((time.perf_counter_ns() - total_embed_start) / 1e6) / len(text_query_batch)
    q_relevant_weights = []
    # 2. Query Qdrant
    batch_dense = result['dense']['data']
    batch_sparse = result['sparse']['data']
    query_results = []
    query_metadata = []
    query_metrics = []
    for idx, query_text in enumerate(text_query_batch):
        q_dense = []
        if 0 < len(batch_dense):
            q_dense = batch_dense[idx] if batch_dense is not None else None
        q_sparse = []
        if 0 < len(batch_sparse):
            q_sparse = batch_sparse[idx] if batch_sparse is not None else None
        
        if 0 < len(relevant_weights_batch):
            if isinstance(relevant_weights_batch, list):
                q_relevant_weights = relevant_weights_batch[idx]
            if isinstance(relevant_weights_batch, dict):
                q_relevant_weights = relevant_weights_batch
            q_relevant_weights = {int(k): v for k, v in q_relevant_weights.items()}
        
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
        retrieved_idx = [point.payload['idx'] for point in query_result]

        resulted_metadata = {}
        resulted_metadata['retrieved-idx'] = retrieved_idx
        resulted_metadata['query-score'] = [point.score for point in query_result]
        resulted_metadata['query-topic'] = [point.payload['topic'] for point in query_result]
        resulted_metadata['query-relevance'] = [int(point.payload['relevance']) for point in query_result]
        resulted_metadata['query-ranking'] = [point.payload['ranking-weights'] for point in query_result]
        resulted_metadata['query-part'] = [int(point.payload['part']) for point in query_result]
        resulted_metadata['query-document'] = [int(point.payload['document']) for point in query_result]
        resulted_metadata['query-chapter'] = [int(point.payload['chapter']) for point in query_result]
        resulted_metadata['query-index'] = [int(point.payload['index']) for point in query_result] 

        resulted_metrics = {} 
        if 0 < len(q_relevant_weights):
            resulted_metrics = evalution_ranking_metrics( 
                retrieved_ids = retrieved_idx,
                true_relevant_weights = q_relevant_weights,
                relevance_threshold = relevance_threshold
            ) 
            resulted_metrics['relevant-weights'] = q_relevant_weights

        resulted_metrics['dense-model'] = dense_model_name
        resulted_metrics['sparse-model'] = sparse_model_name
        resulted_metrics['embedding-latency-ms'] = total_embed_total_ms
        resulted_metrics['search-latency-ms'] = search_latency_ms
        resulted_metrics['total-latency-ms'] = total_embed_total_ms + search_latency_ms
        resulted_metrics['total-characters'] = total_characters

        query_results.append(query_result)
        query_metadata.append(query_metadata)
        query_metrics.append(resulted_metrics)
        
    return {
        'results': query_results,
        'metadata': query_metadata,
        'metrics': query_metrics,
        'dense-mean-time-ms': result['dense']['mean-time-ms'],
        'sparse-mean-time-ms': result['sparse']['mean-time-ms'],
    }

def rag_get_statistics(
    gathered_metrics: dict,
    percentile_filter: list
):
    try:
        import statistics
        import numpy as np
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)
    
    summary_statistics = {}
    for key, value in gathered_metrics.items():
        key_mean_column = f'{key}-mean'
        key_median_column = f'{key}-median'
        key_mean = statistics.mean(value)
        key_median = statistics.median(value)
        summary_statistics[key_mean_column] = float(key_mean)
        summary_statistics[key_median_column] = float(key_median)

        if not key in percentile_filter:
            key_p95_column = f'{key}-p95'
            key_p99_column = f'{key}-p99'
            key_p95 = np.percentile(value, 95)
            key_p99 = np.percentile(value, 99)
            summary_statistics[key_p95_column] = float(key_p95)
            summary_statistics[key_p99_column] = float(key_p99)
    return summary_statistics

def rag_data_metrics(
    dataset_name: str,
    target_df: any,
    query_column: str,
    weigth_column: str,
    qdrant_client: any,
    query_type: str,
    collection_name: str,
    relevance_threshold: float,
    query_limit: int,
    fusion_limit: int,
    dense_model_name: str,
    dense_model: any,
    sparse_model_name: str,
    sparse_model: any,
    batch_size: int,
    debug_prints: bool
):  
    df_text_queries = target_df[query_column].tolist()
    df_relevant_weights = target_df[weigth_column].tolist()
   
    batch_outputs = rag_batch_query(
        qdrant_client = qdrant_client,
        query_type = query_type,
        collection_name = collection_name,
        text_query_batch = df_text_queries, 
        relevant_weights_batch = df_relevant_weights,
        relevance_threshold = relevance_threshold,
        query_limit = query_limit,
        fusion_limit = fusion_limit,
        dense_model = dense_model,
        dense_model_name = dense_model_name,
        sparse_model = sparse_model,
        sparse_model_name = sparse_model_name,
        batch_size = batch_size
    )
    
    print('')
    gathered_metrics = {}
    for j, result, in enumerate(batch_outputs['results']):
        query_text = df_text_queries[j]
        true_relevant_weight = df_relevant_weights[j]
        query_metrics = batch_outputs['metrics'][j]
        
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
            
            print(f'Relevant ids|{true_relevant_weight}')
            print(f"Precision@1|{query_metrics['p@1']}")
            print(f"Recall@3|{query_metrics['r@3']}")
            print(f"RR|{query_metrics['rr']}")
            print(f"AP|{query_metrics['ap']}")
            print(f"NDCG@3|{query_metrics['ndcg@3']}")
            print(f"NDCG@5|{query_metrics['ndcg@5']}")
            print(f"Embedding latency (ms)|{query_metrics['embedding-latency-ms']}")
            print(f"Search latency (ms)|{query_metrics['search-latency-ms']}")
            print(f"Total latency (ms)|{query_metrics['total-latency-ms']}")
            print(f"Total retrieved characters|{query_metrics['total-characters']}")
            print('case|idx|relevance|score|part|document|chapter|index|topic')
            for i, point in enumerate(result, 1):
                p = point.payload
                print(f"{i}|{p.get('idx')}|{p.get('relevance')}|{point.score}|{p.get('part')}|{p.get('document')}|{p.get('chapter')}|{p.get('index')}|{p.get('topic')}")
            print('') 

        for key, value in query_metrics.items():
            if key not in gathered_metrics:
                gathered_metrics[key] = []
            gathered_metrics[key].append(value)
    
    return gathered_metrics