def setup_celery_app():
    from functions.platforms.celery.setup import celery_setup_instance
    from functions.platforms.celery.use import celery_setup_logging
    
    celery_logs = celery_setup_logging()
        
    celery_app = celery_setup_instance()

    from functions.platforms.prometheus.setup import prometheus_create_server

    prometheus_create_server()

    from tasks.interactive.requests import forwarder_requests
    celery_app.task(forwarder_requests)

    from tasks.scheduled.trigger import forwarder_trigger
    celery_app.task(forwarder_trigger)

    return celery_app, celery_logs