from fastapi import APIRouter, Request

from functions.models.parameters import Parameters
from functions.caching import caching_generate_key, caching_save_dict

setup_fastapi = APIRouter(prefix = '/setup')

@setup_fastapi.post("/config")
async def configuration_setup(
    request: Request,
    parameters: Parameters
): 
    request.app.state.logger.info('Configuration setup')

    parameters_dict = parameters.model_dump(by_alias = True)

    parameters_key = caching_generate_key(
        static = True,
        user = 'submitter-fastapi-celery',
        target = 'tasks',
        group = 'dict'
    )
    request.app.state.logger.info(parameters_key)
    storage_parameters = parameters_dict['storage-parameters']
    cache_location = storage_parameters['celery-cache-location']
    cache_parameters = storage_parameters['cache'][cache_location]
    
    cache_response = caching_save_dict(
        cache_parameters = cache_parameters,
        cache_key = parameters_key,
        nested_dict = parameters_dict
    )

    return_dict = {'output': cache_response}
    return return_dict
