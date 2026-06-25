import os

from functions.platforms.celery.setup import celery_setup_instance
from functions.platforms.celery.use import celery_get_logs

from functions.concurrency import concurrency_get_client, concurrency_check_lock, concurrency_get_lock, concurrency_release_lock
from functions.caching import caching_generate_key, caching_get_dict

tasks_celery = celery_setup_instance(
    redis_endpoint = os.environ.get('REDIS_ENDPOINT'),
    redis_port = os.environ.get('REDIS_PORT'),
    redis_db = os.environ.get('REDIS_DB')
)

@tasks_celery.task( 
    bind = False, 
    max_retries = 0,
    soft_time_limit = 120,
    time_limit = 240,
    rate_limit = None,
    name = 'tasks.submitter-trigger'
)
def submitter_trigger():
    return_dict = {}
    try: 
        cache_parameters = {
            'system': 'redis',
            'user': 'part-2',
            'target': 'backend',
            'redis-endpoint': os.environ.get('REDIS_ENDPOINT'),
            'redis-port': os.environ.get('REDIS_PORT'),
            'redis-db': os.environ.get('REDIS_DB')
        }

        parameters_key = caching_generate_key(
            static = True,
            user = cache_parameters['user'],
            target = cache_parameters['target'],
            group = 'dict'
        )

        storage_parameters = caching_get_dict(
            cache_parameters = cache_parameters,
            cache_key = parameters_key
        )

        lock_location = storage_parameters['celery-lock-location']
        lock_parameters = storage_parameters['lock'][lock_location]

        lock_parameters['group'] = 'interactive'
        lock_parameters['resource'] = 'submitter-requests'

        lock_client = concurrency_get_client(
            lock_parameters = lock_parameters
        )

        lock_active, lock_name = concurrency_check_lock(
            lock_parameters = lock_parameters,
            lock_client = lock_client
        )

        if not lock_active:
            lock_created, client_lock = concurrency_get_lock(
                lock_client = lock_client,
                lock_name = lock_name
            )

            if lock_created:
                try:
                    return_dict = {
                        'key': 'value'
                    } 
                except Exception as e:
                    print('Submitter requests error: ' + str(e))
                    
                lock_released = concurrency_release_lock(
                    lock_client = lock_client,
                    client_lock = client_lock
                )
        return return_dict
    except Exception as e:
        print('Submitter trigger error:', e)
        return return_dict