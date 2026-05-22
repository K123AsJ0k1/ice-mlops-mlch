from fastapi import APIRouter, Request

general_fastapi = APIRouter(prefix = '/general')

@general_fastapi.post("/test")  
async def test_route(
    request: Request
):  
    return_dict = {
        'output': 'Test'
    }
    request.app.state.logger.info('Test')
    return return_dict
