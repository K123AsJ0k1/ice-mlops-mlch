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
        sparse_model_name: str
    ):
        from sentence_transformers import SentenceTransformer
        from fastembed import SparseTextEmbedding
        self.dense_model = SentenceTransformer(dense_model_name)
        self.sparse_model = SparseTextEmbedding(
            model_name = sparse_model_name,
            providers = [
                "CUDAExecutionProvider"
            ]
        )
        
    def batch_generate_vectors(
        self,
        worker_index: int,
        actor_index: int,
        data_index: int,
        batch_index: int,
        object_path: str,
        text_inputs: list,
        row_indices: list
    ) -> any:
        from icebreaker.embeddings.use import embeddings_batch_create_vectors
        dense_vectors, sparse_vectors = embeddings_batch_create_vectors(
            text_data = text_inputs,
            dense_model = self.dense_model,
            sparse_model = self.sparse_model,
        )
        
        result = {
            'worker_idx': worker_index,
            'actor_idx': actor_index,
            'data_idx': data_index,
            'batch_idx': batch_index,
            'object_path': object_path,
            'dense': dense_vectors,
            'sparse': sparse_vectors,
            'row_indices': row_indices 
        }

        return result