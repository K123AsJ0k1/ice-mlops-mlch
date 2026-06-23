
def is_minio_client(
    storage_client: any
) -> bool:
    try:
        from minio import Minio
    except ImportError as e:
        raise ImportError("minio/setup failed to import", e)

    return isinstance(storage_client, Minio)

def minio_setup_client(
    endpoint: str,
    username: str,
    password: str
) -> any:
    try:
        from minio import Minio
    except ImportError as e:
        raise ImportError("minio/setup failed to import", e)

    minio_client = Minio(
        endpoint = endpoint, 
        access_key = username, 
        secret_key = password,
        secure = False
    )
    return minio_client