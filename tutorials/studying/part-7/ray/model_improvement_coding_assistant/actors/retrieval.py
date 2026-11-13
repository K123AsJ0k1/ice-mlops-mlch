import ray

@ray.remote(
    num_cpus = 0.2,
    num_gpus = 0.1,
    memory = 0.2 * 1024 * 1024 * 1024
)
class Retrieval:
    def __init__(
        self,
        qdrant_parameters: dict,
        retrieval_parameters: dict
    ): 
        from icebreaker.qdrant.setup import qdrant_setup_client
        from sentence_transformers import SentenceTransformer
        from sentence_transformers import SparseEncoder 
        
        self.qdrant_client = qdrant_setup_client(
            qdrant_parameters = qdrant_parameters
        )
        device_mode = retrieval_parameters['device-mode']

        print(f'Using device mode: {device_mode}')
        
        dense_model_name = retrieval_parameters['dense-model-name']
        print(f'Using dense model: {dense_model_name}')
        self.dense_model = SentenceTransformer(
            dense_model_name, 
            device = device_mode
        )
        self.dense_model_name = dense_model_name

        sparse_model_name = retrieval_parameters['sparse-model-name']
        print(f'Using sparse model: {sparse_model_name}')
        self.sparse_model = SparseEncoder(
            sparse_model_name,
            device = device_mode
        )
        self.sparse_model_name = sparse_model_name

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
        from icebreaker.rag.utility import rag_batch_query

        result = { 
            'key_name': key_name 
        }
        
        batch_outputs = rag_batch_query(
            qdrant_client = self.qdrant_client,
            query_type = query_type,
            collection_name = collection_name,
            text_query_batch = text_query_batch, 
            relevant_weights_batch = relevant_weights_batch,
            relevance_threshold = relevance_threshold,
            query_limit = query_limit,
            fusion_limit = fusion_limit,
            dense_model = self.dense_model,
            sparse_model = self.sparse_model,
            batch_size = batch_size
        )

        result = result | batch_outputs

        return result
