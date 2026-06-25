def sparse_create_simple_tuple(
    global_vocabulary: dict,
    vector_text: str
):
    from collections import Counter
    import re
    
    words = re.findall(r"\b\w+\b", vector_text.lower())
    word_counts = Counter(words)
    
    indices = []
    values = []  
    
    for word, count in word_counts.items():
        if word not in global_vocabulary:
            global_vocabulary[word] = len(global_vocabulary)
        
        indices.append(global_vocabulary[word])
        values.append(float(count))

    return indices, values

def sparse_create_spalde_tuple(
    sparse_model: any,
    vector_text: str
) -> any:
    sparse_embeddings = list(sparse_model.embed([vector_text]))[0]

    indices = sparse_embeddings.indices.tolist()
    values = sparse_embeddings.values.tolist()

    return indices, values
