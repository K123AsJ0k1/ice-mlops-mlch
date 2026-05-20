
def caching_generate_key(
    static: bool,
    user: str,
    target: str,
    group: str
) -> str:
    try:
        import uuid
    except ImportError as e:
        raise ImportError("Failed to import", e)

    key_name = 'cache:' + user + ':' + target + ':' + group
    if not static:
        resource = str(uuid.uuid4())
        key_name += ':' + resource
    return key_name

def caching_save_dict(
    cache_parameters: any,
    cache_key: str,
    nested_dict: any
) -> bool:
    try:
        from .redis.setup import redis_setup_instance
        from .redis.use import redis_store_nested_dict
    except ImportError as e:
        raise ImportError("Failed to import", e)

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

        print('Testing connection: ' + str(redis_endpoint) + ':' + str(redis_port) + ':' + str(redis_db))
        client_connected = redis_client.ping()
        if client_connected:
            print('Using key: ' + str(cache_key))
            cache_response = redis_store_nested_dict(
                redis_client = redis_client,
                dict_name = cache_key,
                nested_dict = nested_dict
            )
    print(cache_system + ' responded with: ' + str(cache_response))
    return cache_response

def caching_get_dict(
    cache_parameters: any,
    cache_key: str,
) -> any:
    try:
        from .redis.setup import redis_setup_instance
        from .redis.use import redis_get_nested_dict
    except ImportError as e:
        raise ImportError("Failed to import", e)

    cache_dict = {}
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

        print('Testing connection: ' + str(redis_endpoint) + ':' + str(redis_port) + ':' + str(redis_db))
        client_connected = redis_client.ping()
        if client_connected:
            print('Using key: ' + str(cache_key))
            cache_dict = redis_get_nested_dict(
                redis_client = redis_client,
                dict_name = cache_key
            )
    print(cache_system + ' gave dict: ' + str(cache_dict))
    return cache_dict

