
def redis_store_nested_dict(
    redis_client: any,
    dict_name: str,
    nested_dict: any
) -> bool:
    try:
        import pickle
    except ImportError as e:
        raise ImportError("Failed to import", e)

    try:
        formatted_dict = pickle.dumps(nested_dict)
        result = redis_client.set(dict_name, formatted_dict)
        return result
    except Exception as e:
        return False

def redis_get_nested_dict(
    redis_client: any,
    dict_name: str
) -> any:
    try:
        import pickle
    except ImportError as e:
        raise ImportError("Failed to import", e)

    try:
        pickled_dict = redis_client.get(dict_name)
        unformatted_dict = pickle.loads(pickled_dict)    
        return unformatted_dict
    except Exception as e:
        return None
    
def redis_lock_interaction(
    redis_client: any,
    redis_lock: any,
    mode: str,
    lock_name: str,
    timeout: int
) -> any:
    first_output = False
    second_output = None
    try:
        if mode == 'check':
            first_output = bool(redis_client.exists(lock_name))
        if mode == 'release':
            if redis_lock.locked():
                redis_lock.release()
                first_output = True
        if mode == 'get':
            lock_instance = redis_client.lock(
                lock_name,
                timeout = timeout
            )

            lock_aquired = lock_instance.acquire(blocking = True)
            
            if lock_aquired:
                first_output = True
                second_output = lock_instance
        return first_output, second_output
    except Exception as e:
        return first_output, second_output

def redis_lock_checking(
    redis_client: any,
    lock_name: any,
    check_tries: int,
    check_timeout: int
):
    try:
        import time as t
    except ImportError as e:
        raise ImportError("Failed to import", e)

    print('Checking lock for ' + str(lock_name))
    lock_active = True
    for i in range(check_tries):
        lock_active, empty_1 = redis_lock_interaction(
            redis_client = redis_client,
            redis_lock = None,
            mode = 'check',
            lock_name = lock_name,
            timeout = 200
        )
        print('Lock active: ' + str(lock_active))
        if not lock_active:
            break
        t.sleep(check_timeout)
    return lock_active

def redis_name_lock(
    user: str,
    place: str,
    group: str,
    resource: str
) -> str:
    lock_name = 'lock:' + user + ':' + place + ':' + group + ':' + resource
    return lock_name