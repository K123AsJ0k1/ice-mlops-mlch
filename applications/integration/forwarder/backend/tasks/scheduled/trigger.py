from functions.platforms.celery.setup import celery_setup_instance

from functions.platforms.redis.setup import redis_setup_instance
from functions.platforms.redis.use import redis_lock_interaction, redis_get_nested_dict

from functions.platforms.airflow.setup import airflow_setup_configuration
from functions.platforms.airflow.use import airflow_trigger_dag

tasks_celery = celery_setup_instance()

@tasks_celery.task( 
    bind = False, 
    max_retries = 0,
    soft_time_limit = 120,
    time_limit = 240,
    rate_limit = '2/m',
    name = 'tasks.forwarder-trigger'
)
def forwarder_trigger():
    return_dict = {}
    try: 
        redis_client = redis_setup_instance()

        parameters_dict = redis_get_nested_dict(
            redis_client = redis_client,
            dict_name = 'dict-forwarder-parameters'
        ) 
        
        lock_name = 'lock-forwarder-trigger'
        redis_lock = None

        lock_active, empty_1 = redis_lock_interaction(
            redis_client = redis_client,
            redis_lock = None,
            mode = 'check',
            lock_name = lock_name,
            timeout = 200
        ) 

        if not lock_active:
            lock_created, redis_lock = redis_lock_interaction(
                redis_client = redis_client,
                redis_lock = None,
                mode = 'get',
                lock_name = lock_name,
                timeout = 200
            )
            if lock_created:
                try:
                    airflow_configuration = airflow_setup_configuration()
                    return_dict = airflow_trigger_dag(
                        airflow_configuration = airflow_configuration,
                        dag_id = 'tutorial-main',
                        parameters = {
                            'token': 'test',
                            'user': 'user@example.com',
                            'message': 'hello', 
                            'target': 'airflow'
                        }
                    )
                except Exception as e:
                    print(e) 
                lock_released, empty_2 = redis_lock_interaction(
                    redis_client = None,
                    redis_lock = redis_lock,
                    mode = 'release',
                    lock_name = None,
                    timeout = None
                )
        return return_dict
    except Exception as e:
        return return_dict
