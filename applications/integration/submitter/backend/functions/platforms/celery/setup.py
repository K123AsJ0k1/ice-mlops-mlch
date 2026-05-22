from celery import Celery

def celery_setup_instance(
    redis_endpoint: str,
    redis_port: str,
    redis_db: str
):
    name = 'tasks'
    redis_connection = 'redis://' + redis_endpoint + ':' + str(redis_port) + '/' + str(redis_db)

    celery_app = Celery(
        main = name,
        broker = redis_connection,
        backend = redis_connection
    )

    celery_app.conf.broker_connection_retry_on_startup = True
    #celery_app.conf.enable_utc = True
    #celery_app.conf.timezone = 'Europe/Helsinki'

    return celery_app
