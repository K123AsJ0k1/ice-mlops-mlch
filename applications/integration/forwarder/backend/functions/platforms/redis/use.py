import pickle

def redis_store_nested_dict(
    redis_client: any,
    dict_name: str,
    nested_dict: any
) -> bool:
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
    