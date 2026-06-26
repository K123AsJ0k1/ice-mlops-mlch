
def search_binary_retrieval_metrics(
    retrieved_ids: list, 
    true_relevant_ids: list
):
    try: 
        import numpy as np
    except ImportError as e:
        raise ImportError("qdrant/utility failed to import", e)
    # This is binary relevance metrics
    # Convert to set for O(1) membership lookups
    true_set = set(true_relevant_ids)
    total_relevant_count = len(true_set)

    # 1. Generate binary relevance vector based on your structural rules
    relevance = [1 if _id in true_set else 0 for _id in retrieved_ids]
    
    # 2. Precision@1
    # Handle edge case where retrieved_ids might be empty
    p_at_1 = relevance[0] if relevance else 0

    # 3. Recall@3
    # Multi-doc logic: (number of matches in top 3) / (total number of expected matches in database)
    if total_relevant_count > 0:
        r_at_3 = float(sum(relevance[:3]) / total_relevant_count)
    else:
        r_at_3 = 0.0

    # 4. DCG / NDCG Helper Functions
    def compute_dcg(rel):
        return sum([r / np.log2(idx + 2) for idx, r in enumerate(rel)])
    
    def compute_idcg(k):
        # The ideal relevance distribution ranks all matches perfectly at the top.
        # If total_relevant_count is 2 and k is 5, the ideal list is [1, 1, 0, 0, 0]
        ideal_relevance = [1 if i < total_relevant_count else 0 for i in range(k)]
        return compute_dcg(ideal_relevance)

    # Compute Actual DCG values
    dcg_3 = compute_dcg(relevance[:3])
    dcg_5 = compute_dcg(relevance[:5])
    
    # Compute Ideal DCG values dynamically based on total_relevant_count
    idcg_3 = compute_idcg(3)
    idcg_5 = compute_idcg(5)
    
    # Normalize (Guard against division by zero if there are no ground truth docs)
    ndcg_3 = float(dcg_3 / idcg_3) if idcg_3 > 0 else 0.0
    ndcg_5 = float(dcg_5 / idcg_5) if idcg_5 > 0 else 0.0
   
    resulted_metrics = {
        'p@1': p_at_1,
        'r@3': r_at_3,
        'ndcg@3': ndcg_3,
        'ndcg@5': ndcg_5
    }
    
    return resulted_metrics

def search_weighted_retrieval_metrics(
    retrieved_ids: list, 
    true_relevant_weights: dict
):
    try: 
        import numpy as np
    except ImportError as e:
        raise ImportError("qdrant/utility failed to import", e)

    # Convert dictionary values to handle lookup and metrics tracking
    # Counts how many documents are strictly relevant (grade > 0)
    total_relevant_count = sum(1 for grade in true_relevant_weights.values() if grade > 0)

    # 1. Generate graded relevance vector
    relevance = [true_relevant_weights.get(_id, 0) for _id in retrieved_ids]
    
    # 2. Precision@1 Proxy
    # Binary interpretation: Was the first retrieved item relevant at all (grade > 0)?
    p_at_1 = 1 if relevance and relevance[0] > 0 else 0

    # 3. Recall@3 Proxy
    # Fraction of all relevant ground-truth docs found in the top 3 (regardless of specific grade)
    if total_relevant_count > 0:
        hits_in_top_3 = sum(1 for grade in relevance[:3] if grade > 0)
        r_at_3 = float(hits_in_top_3 / total_relevant_count)
    else:
        r_at_3 = 0.0

    # 4. Graded DCG / NDCG Helper Functions
    def compute_graded_dcg(rel_vector):
        # Using standard 2^rel - 1 gain optimization to favor higher grades heavily
        return sum([((2**r) - 1) / np.log2(idx + 2) for idx, r in enumerate(rel_vector)])
    
    def compute_graded_idcg(k):
        # Sort ALL available ground truth weights in descending order to establish the ideal vector
        sorted_weights = sorted(true_relevant_weights.values(), reverse=True)
        
        # Pad with zeros if there are fewer ground truth items available than k elements requested
        ideal_relevance = (sorted_weights + [0] * k)[:k]
        return compute_graded_dcg(ideal_relevance)

    # Compute Actual DCG values from your retriever output
    dcg_3 = compute_graded_dcg(relevance[:3])
    dcg_5 = compute_graded_dcg(relevance[:5])
    
    # Compute Ideal DCG values dynamically based on best available documents
    idcg_3 = compute_graded_idcg(3)
    idcg_5 = compute_graded_idcg(5)
    
    # Normalize (Guard against division by zero if no ground truth docs are provided)
    ndcg_3 = float(dcg_3 / idcg_3) if idcg_3 > 0 else 0.0
    ndcg_5 = float(dcg_5 / idcg_5) if idcg_5 > 0 else 0.0
    
    resulted_metrics = {
        'p@1-proxy': p_at_1,
        'r@3-proxy': r_at_3,
        'ndcg@3-graded': ndcg_3,
        'ndcg@5-graded': ndcg_5
    } 
    
    return resulted_metrics

def search_get_statistics(
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