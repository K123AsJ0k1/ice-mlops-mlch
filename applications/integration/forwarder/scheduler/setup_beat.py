import os
from celery.schedules import timedelta

def setup_beat_app():
    from functions.platforms.celery.setup import celery_setup_instance

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
        'forwarder-trigger': {
            'task': 'tasks.forwarder-trigger',
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