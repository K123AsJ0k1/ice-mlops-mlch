
def dense_create_baai_vectors(
    dense_model: any,
    text_inputs: list
) -> any:
    dense_vectors = dense_model.encode(
        text_inputs, 
        normalize_embeddings = True
    ).tolist()
    return dense_vectors