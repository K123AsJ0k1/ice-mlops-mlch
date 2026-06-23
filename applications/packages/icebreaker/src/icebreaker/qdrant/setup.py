
def qdrant_is_client(
    storage_client: any
) -> any:
    try:
        from qdrant_client import QdrantClient as qc
    except ImportError as e:
        raise ImportError("qdrant/setup failed to import", e)

    try:
        return isinstance(storage_client, qc.Connection)
    except Exception as e:
        return False

def qdrant_setup_client(
    api_key: str,
    address: str, 
    port: str
) -> any:
    try:
        from qdrant_client import QdrantClient as qc
    except ImportError as e:
        raise ImportError("qdrant/setup failed to import", e)

    try:
        qdrant_client = qc(
            host = address,
            port = int(port),
            api_key = api_key,
            https = False
        ) 
        return qdrant_client
    except Exception as e:
        return None