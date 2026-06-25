from functions.platforms.redis.setup import redis_client_check, redis_setup_instance
from functions.platforms.redis.use import redis_lock_interaction, redis_lock_checking, redis_name_lock

def concurrency_get_client(
    lock_parameters: any
) -> bool:
    lock_client = None
    client_connected = False
    lock_system = lock_parameters['system']
    if lock_system == 'redis':
        redis_endpoint = lock_parameters['redis-endpoint']
        redis_port = lock_parameters['redis-port']
        redis_db = lock_parameters['redis-db']
        lock_client = redis_setup_instance(
            redis_endpoint = redis_endpoint,
            redis_port = redis_port,
            redis_db = redis_db
        )
        print('Testing connection: ' + str(redis_endpoint) + ':' + str(redis_port) + ':' + str(redis_db))
        client_connected = lock_client.ping()
    print(lock_system + ' connected: ' + str(client_connected))
    return lock_client
    
def concurrency_check_lock(
    lock_parameters: any,
    lock_client: any
) -> any:
    lock_active = False
    lock_name = ''
    if not lock_client is None:
        if redis_client_check(storage_client = lock_client):
            lock_name = redis_name_lock(
                user = lock_parameters['user'],
                target = lock_parameters['target'],
                group = lock_parameters['group'],
                resource = lock_parameters['resource']
            )
            lock_active = redis_lock_checking(
                redis_client = lock_client,
                lock_name = lock_name,
                check_tries = 40,
                check_timeout = 1
            )
    print('Lock ' + str(lock_name) + ' active: ' + str(lock_active))
    return lock_active, lock_name

def concurrency_get_lock(
    lock_client: any,
    lock_name: str
) -> any:
    lock_created = False
    client_lock = None
    if redis_client_check(storage_client = lock_client):
        lock_created, client_lock = redis_lock_interaction(
            redis_client = lock_client,
            redis_lock = None,
            mode = 'get',
            lock_name = lock_name,
            timeout = 200
        )
    print('Lock created: ' + str(lock_created))
    return lock_created, client_lock

def concurrency_release_lock(
    lock_client: any,
    client_lock: any
) -> bool:
    lock_released = False
    if redis_client_check(storage_client = lock_client):
        lock_released, empty_2 = redis_lock_interaction(
            redis_client = None,
            redis_lock = client_lock,
            mode = 'release',
            lock_name = None,
            timeout = None
        )
    print('Lock released: ' + str(lock_released))
    return lock_released