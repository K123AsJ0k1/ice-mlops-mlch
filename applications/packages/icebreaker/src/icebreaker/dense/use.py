
def dense_create_baai_vectors(
    dense_model: any,
    text_inputs: list,
    batch_size: int
) -> any:
    dense_vectors = dense_model.encode(
        text_inputs, 
        batch_size = batch_size,
        normalize_embeddings = True
    ).tolist() 
    return dense_vectors 