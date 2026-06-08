import redis

def redis_client_check(
    storage_client: any
) -> any:
    return isinstance(storage_client, redis.Redis)

def redis_setup_instance(
    redis_endpoint: str,
    redis_port: str,
    redis_db: str
):
    redis_client = redis.Redis(
        host = redis_endpoint,
        port = int(redis_port),
        db = redis_db
    )
    return redis_client