import os
from celery import Celery
from celery.schedules import timedelta

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

def setup_beat_app():
    beat_app = celery_setup_instance()

    schelude_absolute_path = os.path.abspath('celerybeat-schedule')
    
    if os.path.exists(schelude_absolute_path):
        os.remove(schelude_absolute_path)

    task_times = os.environ.get('SCHEDULER_TIMES').split('|')
    schedule = []
    expires_seconds = []
    for time in task_times:
        schedule.append(timedelta(seconds = int(time)))
        expires_seconds.append(int(time))
    
    beat_app.conf.beat_schedule = {
        'submitter-trigger': {
            'task': 'tasks.submitter-trigger',
            'schedule': schedule[0],
            'kwargs': {},
            'relative': True,
            'options': {
                'expire_seconds': expires_seconds[0]
            }
        }
    }

    beat_app.conf.timezone = 'UTC'
    return beat_app 