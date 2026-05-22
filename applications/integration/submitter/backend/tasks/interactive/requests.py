import os

from functions.platforms.celery.setup import celery_setup_instance
from functions.platforms.celery.use import celery_get_logs

from functions.platforms.airflow.setup import airflow_setup_configuration
from functions.platforms.airflow.use import airflow_trigger_dag, airflow_wait_task

from functions.caching import caching_generate_key, caching_get_dict

from functions.locking import concurrency_get_client, concurrency_check_lock, concurrency_get_lock, concurrency_release_lock

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
                    if mode == 'orch':
                        cache_location = storage_parameters['celery-cache-location']
                        cache_parameters = storage_parameters['cache'][cache_location]

                        parameters_key = caching_generate_key(
                            static = True,
                            user = 'submitter-fastapi-celery',
                            target = 'tasks',
                            group = 'dict'
                        )
                        print(parameters_key)
                        parameters_dict = caching_get_dict(
                            cache_parameters = cache_parameters,
                            cache_key = parameters_key
                        )

                        swift_paramters = parameters_dict['swift-parameters']
                        bucket_parameters = parameters_dict['bucket-parameters']
                        
                        cache_key = caching_generate_key(
                            static = False,
                            user = 'submitter-celery-airflow',
                            target = 'storage-interaction',
                            group = 'dict'
                        )

                        storage_parameters['cache-key'] = cache_key
                        triggered_dag = airflow_trigger_dag(
                            airflow_configuration = airflow_setup_configuration(),
                            dag_id = 'submitter-storage-interaction',
                            parameters = {
                                'swift-parameters': swift_paramters,
                                'bucket-parameters':  bucket_parameters,
                                'storage-parameters': storage_parameters
                            }
                        )
                        
                        dag_status = airflow_wait_task(
                            airflow_configuration = airflow_setup_configuration(),
                            dag_id = 'submitter-storage-interaction',
                            run_id = triggered_dag['id'],
                            limit = 4,
                            tries = 10,
                            timeout = 2
                        )
 
                        if dag_status:
                            return_dict = caching_get_dict(
                                cache_parameters = cache_parameters,
                                cache_key = cache_key
                            )
                            
                except Exception as e:
                    print('Submitter requests error: ' + str(e))
                    
                lock_released = concurrency_release_lock(
                    lock_client = lock_client,
                    client_lock = client_lock
                )
        return return_dict
    except Exception as e:
        return return_dict