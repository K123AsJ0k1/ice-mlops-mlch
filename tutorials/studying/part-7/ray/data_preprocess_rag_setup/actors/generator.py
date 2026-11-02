import ray

@ray.remote(
    num_cpus = 1,
    num_gpus = 1,
    memory = 0.2 * 1024 * 1024 * 1024
)
class Generator:
    def __init__(
        self,
        device_mode: str,
        dense_model_name: str,
        sparse_model_name: str
    ): 
        from sentence_transformers import SentenceTransformer
        from sentence_transformers import SparseEncoder

        self.dense_model = SentenceTransformer(
            dense_model_name, 
            device = device_mode
        )
        self.dense_model_name = dense_model_name
        
        self.sparse_model = SparseEncoder(
            sparse_model_name,
            device = device_mode
        )
        self.sparse_model_name = sparse_model_name

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
