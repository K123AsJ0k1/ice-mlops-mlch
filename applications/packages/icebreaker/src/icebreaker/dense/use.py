
def dense_create_baai_vector(
    dense_model: any,
    vector_text: str
) -> any:
    dense_vector = dense_model.encode(
        vector_text, 
        normalize_embeddings = True
    ).tolist()
    return dense_vector