from fastapi import APIRouter, Request

from functions.models.parameters import Parameters
from functions.models.scheduler import Scheduler
from functions.platforms.redis.use import redis_store_nested_dict
from typing import Dict

setup_fastapi = APIRouter(prefix = '/setup')

@setup_fastapi.post("/config/{mode}")
async def configuration_setup(
    request: Request,
    mode: str,
    input: Dict = {}
): 
    request.app.state.logger.info('Configuration setup')

    return_dict = {'output': None}
    if mode == 'init':
        parameters_dict = Parameters(**input)
        parameters_dict = parameters_dict.model_dump(by_alias = True)

        redis_response = redis_store_nested_dict(
            redis_client = request.app.state.redis,
            dict_name = 'dict-forwarder-parameters',
            nested_dict = parameters_dict
        )

        if redis_response:
            # Start up DAG
            pass
    if mode == 'start':
        scheduler_dict = Scheduler(**input)
        scheduler_dict = scheduler_dict.model_dump(by_alias = True)
        # Scheduler deploy DAG
        pass
    if mode == 'stop':
        # Scheduler remove DAG
        pass
    return return_dict