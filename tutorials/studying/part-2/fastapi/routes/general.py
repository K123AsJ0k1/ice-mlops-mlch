from fastapi import APIRouter, Request

from functions.platforms.logger.use import logger_get_logs

general_fastapi = APIRouter(prefix = '/general')

@general_fastapi.get("/logs")  
async def get_logs(
    request: Request
):  
    request.app.state.logger.info('Get logs')
    return_dict = {
        'output': None
    } 
    return_dict['output'] = logger_get_logs(
        log_path = request.app.state.log_path
    )
    return return_dict