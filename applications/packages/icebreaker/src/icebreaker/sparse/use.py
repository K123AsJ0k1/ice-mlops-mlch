def sparse_create_tuple(
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