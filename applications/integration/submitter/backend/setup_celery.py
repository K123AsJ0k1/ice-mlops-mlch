import os 

def setup_celery_app():
    from functions.platforms.celery.setup import celery_setup_instance
    from functions.platforms.celery.use import celery_setup_logging

    celery_log_path = celery_setup_logging()
    
    celery_app = celery_setup_instance(
        redis_endpoint = os.environ.get('REDIS_ENDPOINT'),
        redis_port = os.environ.get('REDIS_PORT'),
        redis_db = os.environ.get('REDIS_DB')
    )

    from tasks.interactive.requests import submitter_requests
    celery_app.task(submitter_requests)

    from tasks.scheduled.trigger import submitter_trigger
    celery_app.task(submitter_trigger)

    return celery_app, celery_log_path 