import os
from fastapi import FastAPI

def setup_fastapi_app():
    from functions.platforms.logger.setup import logger_initilize
    log_path = 'logs/frontend.log'
    logger = logger_initilize(
        log_path = log_path,
        logger_name = 'submitter-frontend'
    )

    logger.info('Creating FastAPI instance')

    fastapi_app = FastAPI()

    fastapi_app.state.log_path = log_path
    fastapi_app.state.logger = logger

    fastapi_app.state.logger.info('FastAPI created')

    fastapi_app.state.logger.info('Connecting to redis')

    from functions.platforms.redis.setup import redis_setup_instance

    fastapi_app.state.redis = redis_setup_instance(
        redis_endpoint = os.environ.get('REDIS_ENDPOINT'),
        redis_port = os.environ.get('REDIS_PORT'),
        redis_db = os.environ.get('REDIS_DB')
    )

    fastapi_app.state.logger.info('Redis connected')

    fastapi_app.state.logger.info('Defining Celery client')

    from functions.platforms.celery.setup import celery_setup_instance

    fastapi_app.state.celery = celery_setup_instance(
        redis_endpoint = os.environ.get('REDIS_ENDPOINT'),
        redis_port = os.environ.get('REDIS_PORT'),
        redis_db = os.environ.get('REDIS_DB')
    )

    fastapi_app.state.logger.info('Celery client defined')

    fastapi_app.state.logger.info('Importing routes')

    from routes.general import general_fastapi
    from routes.interaction import interaction_fastapi
    from routes.setup import setup_fastapi
    
    fastapi_app.state.logger.info('Including routers')
    
    fastapi_app.include_router(general_fastapi)
    fastapi_app.include_router(interaction_fastapi)
    fastapi_app.include_router(setup_fastapi)
    
    fastapi_app.state.logger.info('Routes implemented')
    
    fastapi_app.state.logger.info('Frontend ready')
    return fastapi_app