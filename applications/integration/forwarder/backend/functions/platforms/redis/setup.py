import os
import redis

def redis_setup_instance():
    redis_endpoint = os.environ.get('REDIS_ENDPOINT')
    redis_port = os.environ.get('REDIS_PORT')
    redis_db = os.environ.get('REDIS_DB')
    redis_client = redis.Redis(
        host = redis_endpoint,
        port = int(redis_port),
        db = redis_db
    )
    return redis_client