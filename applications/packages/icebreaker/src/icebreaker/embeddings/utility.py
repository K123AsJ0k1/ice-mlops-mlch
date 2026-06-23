
def embeddings_generate_hash(
    chunk: any
) -> any:
    try:
        import re
        import hashlib
    except ImportError as e:
        raise ImportError("embeddings/utility failed to import", e)

    chunk = re.sub(r'[^\w\s]', '', chunk)
    chunk = re.sub(r'\s+', ' ', chunk) 
    chunk = chunk.strip()
    chunk = chunk.lower()
    return hashlib.md5(chunk.encode('utf-8')).hexdigest()

def embeddings_generate_uuid(
    id: str,
    index: int
) -> str:
    try:
        import uuid
    except ImportError as e:
        raise ImportError("embeddings/utility failed to import", e)
    keyword_id = id + '-' + str(index + 1)
    keyword_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, keyword_id))
    return keyword_uuid