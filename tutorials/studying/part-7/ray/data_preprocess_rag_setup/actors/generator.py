import ray

@ray.remote(
    num_cpus = 1,
    num_gpus = 1,
    memory = 0.2 * 1024 * 1024 * 1024
)
class Generator:
    def __init__(
        self,
        dense_model_name: str,
        sparse_model_name: str,
        qdrant_parameters: dict
    ): 
        from sentence_transformers import SentenceTransformer
        from sentence_transformers import SparseEncoder
        from icebreaker.qdrant.setup import qdrant_setup_client
        
        self.dense_model = SentenceTransformer(
            dense_model_name, 
            device = "cuda"
        )

        self.dense_model_name = dense_model_name
        
        self.sparse_model = SparseEncoder(
            sparse_model_name,
            device = "cuda"
        )
        self.sparse_model_name = self.sparse_model

        self.qdrant_client = qdrant_setup_client(
            qdrant_parameters = qdrant_parameters
        )

    def batch_generate_vectors(
        self,
        worker_index: int,
        actor_index: int,
        data_index: int,
        batch_index: int,
        key_name: str,
        text_input_batch: list,
        batch_size: int,
        row_indices: list
    ) -> any:
        from icebreaker.embeddings.use import embeddings_batch_create_vectors
        
        result = {
            'worker_idx': worker_index,
            'actor_idx': actor_index,
            'data_idx': data_index,
            'batch_idx': batch_index,
            'key_name': key_name,
            'row_indices': row_indices 
        }
        
        vectors = embeddings_batch_create_vectors(
            text_input_batch = text_input_batch,
            dense_model = self.dense_model,
            sparse_model = self.sparse_model,
            batch_size = batch_size
        )

        result = result | vectors
        
        return result

    def batch_generate_queries(
        self,
        key_name: str,
        query_type: str,
        collection_name: str,
        text_query_batch: list,
        relevant_weights_batch: list,
        relevance_threshold: float,
        query_limit: int,
        fusion_limit: int,
        batch_size: int,
    ) -> any:
        import json
        from icebreaker.rag.utility import rag_batch_query

        result = {
            'key_name': key_name
        }
        
        formatted_weights = []
        for weight in relevant_weights_batch:
            formatted_weights.append(json.loads(weight))

        batch_outputs = rag_batch_query(
            qdrant_client = self.qdrant_client,
            query_type = query_type,
            collection_name = collection_name,
            text_query_batch = text_query_batch, 
            relevant_weights_batch = formatted_weights,
            relevance_threshold = relevance_threshold,
            query_limit = query_limit,
            fusion_limit = fusion_limit,
            dense_model = self.dense_model,
            sparse_model = self.sparse_model,
            batch_size = batch_size
        )

        result = result | batch_outputs

        return result
