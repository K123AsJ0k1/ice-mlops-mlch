import uuid

from functions.platforms.redis.setup import redis_setup_instance
from functions.platforms.redis.use import redis_store_nested_dict

def caching_generate_key(
    static: bool,
    user: str,
    target: str,
    group: str
):
    key_name = 'cache:' + user + ':' + target + ':' + group
    if not static:
        resource = str(uuid.uuid4())
        key_name += ':' + resource
    return key_name

def caching_save_dict(
    logger: any,
    cache_parameters: any,
    cache_key: str,
    nested_dict: any
) -> bool:
    cache_response = False
    cache_system = cache_parameters['system']
    if cache_system == 'redis':
        redis_endpoint = cache_parameters['redis-endpoint']
        redis_port = cache_parameters['redis-port']
        redis_db = cache_parameters['redis-db']

        redis_client = redis_setup_instance(
            redis_endpoint = redis_endpoint,
            redis_port = redis_port,
            redis_db = redis_db
        )

        logger.info('Testing connection: ' + str(redis_endpoint) + ':' + str(redis_port) + ':' + str(redis_db))
        client_connected = redis_client.ping()
        if client_connected:
            logger.info('Using key: ' + str(cache_key))
            cache_response = redis_store_nested_dict(
                redis_client = redis_client,
                dict_name = cache_key,
                nested_dict = nested_dict
            )
    logger.info(cache_system + ' responded with: ' + str(cache_response))
    return cache_response
