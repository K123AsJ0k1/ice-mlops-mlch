
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
    qdrant_parameters: any
) -> any:
    try:
        from qdrant_client import QdrantClient as qc
    except ImportError as e:
        raise ImportError("qdrant/setup failed to import", e)

    try:
        qdrant_client = qc( 
            host = qdrant_parameters['host'],
            port = int(qdrant_parameters['port']),
            api_key = qdrant_parameters['api-key'],
            https = False
        ) 
        return qdrant_client
    except Exception as e:
        return None