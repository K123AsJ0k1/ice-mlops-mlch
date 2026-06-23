import ray

@ray.remote(
    num_gpus = 1
)
class Generator:
    def __init__(
        self,
        hf_token: str,
        embedding_model: str
    ):
        import torch
        from langchain_huggingface import HuggingFaceEmbeddings
    
        print('Starting generator')
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print('GPU device: ' + str(device))
        
        print('Embedding model setup')
        self.embedding_model = HuggingFaceEmbeddings(
            model_name = embedding_model,
            model_kwargs = {
                "device": device
            }
        )
        print('Embedding model ready')
        
    def batch_create_embeddings(
        self,
        batched_chunks: any
    ) -> any:
        batched_embeddings = []
        for tuple in batched_chunks:
            try: 
                list_index = tuple[0]
                chunks = tuple[-1]
                embeddings = self.embedding_model.embed_documents(
                    texts = chunks
                )
                batched_embeddings.append((list_index, embeddings))
            except Exception as e:
                print(e)
        batched_embeddings_ref = ray.put(batched_embeddings)
        return batched_embeddings_ref
    