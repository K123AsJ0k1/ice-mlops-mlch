
def search_retrieval_metrics(
    retrieved_ids: list, 
    true_id: int
):
    try:
        import numpy as np
    except ImportError as e:
        raise ImportError("qdrant/utility failed to import", e)

    relevance = [1 if _id == true_id else 0 for _id in retrieved_ids]
    # Update to have multiple relevance
    p_at_1 = relevance[0]
    r_at_3 = 1.0 if sum(relevance[:3]) > 0 else 0.0
    
    def compute_dcg(rel):
        return sum([r / np.log2(idx + 2) for idx, r in enumerate(rel)])
    
    dcg_3 = compute_dcg(relevance[:3])
    dcg_5 = compute_dcg(relevance[:5])
    
    ndcg_3 = float(dcg_3 / 1.0)
    ndcg_5 = float(dcg_5 / 1.0)
   
    resulted_metrics = {
        'p@1': p_at_1,
        'r@3': r_at_3,
        'ndcg@3': ndcg_3,
        'ndcg@5': ndcg_5
    }
    
    return resulted_metrics