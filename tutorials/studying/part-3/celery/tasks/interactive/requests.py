import os

from functions.platforms.celery.setup import celery_setup_instance
from functions.platforms.celery.use import celery_get_logs

from functions.concurrency import concurrency_get_client, concurrency_check_lock, concurrency_get_lock, concurrency_release_lock

tasks_celery = celery_setup_instance(
    redis_endpoint = os.environ.get('REDIS_ENDPOINT'),
    redis_port = os.environ.get('REDIS_PORT'),
    redis_db = os.environ.get('REDIS_DB')
)

@tasks_celery.task( 
    bind = False, 
    max_retries = 0,
    soft_time_limit = 60,
    time_limit = 120,
    rate_limit = None,
    name = 'tasks.submitter-requests'
) 
def submitter_requests( 
    mode: str,
    input: any 
):   
    return_dict = {}
    try: 
        storage_parameters = input
        
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
                    if mode == 'logs':
                        return_dict = celery_get_logs() 
                except Exception as e:
                    print('Submitter requests error: ' + str(e))
                    
                lock_released = concurrency_release_lock(
                    lock_client = lock_client,
                    client_lock = client_lock
                )

        return return_dict
    except Exception as e:
        print('Submitter requests error', e)
        return return_dict