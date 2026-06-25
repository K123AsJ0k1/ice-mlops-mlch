from fastapi import APIRouter, Request

from functions.models.parameters import Parameters
from functions.caching import caching_generate_key, caching_save_dict

setup_fastapi = APIRouter(prefix = '/setup')

@setup_fastapi.post("/config")
async def post_configuration(
    request: Request,
    parameters: Parameters
): 
    request.app.state.logger.info('Post configuration')
    parameters_dict = parameters.model_dump(by_alias = True)
    storage_parameters = parameters_dict['storage-parameters']

    cache_location = storage_parameters['cache-location']
    cache_parameters = storage_parameters['cache'][cache_location]
    
    parameters_key = caching_generate_key(
        static = True,
        user = cache_parameters['user'],
        target = cache_parameters['target'],
        group = 'dict'
    )
    request.app.state.logger.info(parameters_key)
    
    cache_response = caching_save_dict(
        logger = request.app.state.logger,
        cache_parameters = cache_parameters,
        cache_key = parameters_key,
        nested_dict = parameters_dict
    )

    return_dict = {'output': cache_response}
    return return_dict
