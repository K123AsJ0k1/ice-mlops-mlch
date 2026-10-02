def qdrant_simple_hybrid_config():
    try:
        from qdrant_client.models import models
    except ImportError as e:
        raise ImportError("qdrant/use failed to import", e)

    try:
        hybrid_search_config = {
            'vectors-config': {
                "dense": models.VectorParams(size=384, distance=models.Distance.COSINE)
            },
            'sparse-vectors-config': {
                "sparse": models.SparseVectorParams(
                    index=models.SparseIndexParams(on_disk=False)
                )
            }
        }
        return hybrid_search_config
    except Exception as e:
        print(f"Error hybrid config: {e}")
        return None
    
def qdrant_default_hybrid_config():
    try:
        from qdrant_client.models import models
    except ImportError as e:
        raise ImportError("qdrant/use failed to import", e)

    try:
        hybrid_search_config = {
            'vectors-config': {
                "dense": models.VectorParams(size=384, distance=models.Distance.COSINE)
            },
            'sparse-vectors-config': {
                "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)
            }
        }
        return hybrid_search_config
    except Exception as e:
        print(f"Error hybrid config: {e}")
        return None
    
def qdrant_baai_hybrid_config():
    try:
        from qdrant_client.models import models
    except ImportError as e:
        raise ImportError("qdrant/use failed to import", e)

    try:
        hybrid_search_config = {
            'vectors-config': {
                "dense": models.VectorParams(size=1024, distance=models.Distance.COSINE)
            },
            'sparse-vectors-config': {
                "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)
            }
        }
        return hybrid_search_config
    except Exception as e:
        print(f"Error hybrid config: {e}")
        return None

def qdrant_hybrid_config():
    try:
        from qdrant_client.models import Distance, VectorParams, SparseVectorParams
    except ImportError as e:
        raise ImportError("qdrant/use failed to import", e)

    try:
        hybrid_search_config = {
            "dense-vectors-config": {
                "dense": VectorParams(
                    size = 768,  
                    distance = Distance.COSINE
                )
            },
            "sparse-vectors-config": {
                "sparse": SparseVectorParams()  
            }
        }
        return hybrid_search_config
    except Exception as e:
        print(f"Error building hybrid config: {e}")
        return None