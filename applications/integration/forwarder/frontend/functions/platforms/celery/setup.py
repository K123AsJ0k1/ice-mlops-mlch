import os

from celery import Celery

def celery_setup_instance():
    redis_endpoint = os.environ.get('REDIS_ENDPOINT')
    redis_port = os.environ.get('REDIS_PORT')
    redis_db = os.environ.get('REDIS_DB')
    
    name = 'tasks'
    redis_connection = 'redis://' + redis_endpoint + ':' + str(redis_port) + '/' + str(redis_db)

    celery_app = Celery(
        main = name,
        broker = redis_connection,
        backend = redis_connection
    )

    celery_app.conf.broker_connection_retry_on_startup = True

    return celery_app
