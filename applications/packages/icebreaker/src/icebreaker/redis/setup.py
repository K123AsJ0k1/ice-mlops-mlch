def redis_client_check(
    storage_client: any
) -> any:
    try:
        import redis
    except ImportError as e:
        raise ImportError("Failed to import", e)

    return isinstance(storage_client, redis.Redis)

def redis_setup_instance(
    redis_endpoint: str,
    redis_port: str,
    redis_db: str
):
    try:
        import redis
    except ImportError as e:
        raise ImportError("Failed to import", e)

    redis_client = redis.Redis(
        host = redis_endpoint,
        port = int(redis_port),
        db = redis_db
    )
    return redis_client