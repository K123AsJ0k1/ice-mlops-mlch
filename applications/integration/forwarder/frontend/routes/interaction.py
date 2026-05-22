from fastapi import APIRouter, Request

from functions.models.orchestration import Orchestration
from functions.models.forwarding import Forwarding
from functions.platforms.celery.use import celery_get_id, celery_get_task, celery_await_signature
from functions.platforms.logger.use import logger_get_logs
from typing import Union, Dict

interaction_fastapi = APIRouter(prefix = '/interaction')

@interaction_fastapi.get("/task/{type}/{identity}")
async def task_interaction(
    request: Request,
    type: str,
    identity: str,
    input: Dict = {}
):
    request.app.state.logger.info('Task interaction')
    
    suitable_types = [
        'run',
        'get'
    ]

    return_dict = {
        'output': None
    }

    if type in suitable_types:
        if type == suitable_types[0]:
            #print('Run')
            #print(identity)
            task_id = celery_get_id(
                task_name = identity,
                task_kwargs = input
            )
            return_dict['output'] = task_id
        if type == suitable_types[1]:
            #print('Get')
            task_data = celery_get_task( 
                celery_client = request.app.state.celery,
                task_id = identity
            )
            return_dict['output'] = task_data
    #print(return_dict)
    return return_dict

@interaction_fastapi.post("/orch/{type}/{key}")
async def orchestration_interaction(
    request: Request,
    type: str,
    key: str,
    input: Union[Orchestration,dict] = {}
):  
    request.app.state.logger.info('Orchestration interaction')

    task_payload = {
        'mode': None,
        'type': None,
        'input': None
    }

    suitable_types = [
        'submit',
        'start',
        'stop'
    ]

    return_dict = {
        'output': None
    }
    
    if type in suitable_types:
        task_payload['mode'] = 'orchestration'
        task_payload['type'] = type
        if type == suitable_types[0]:
            #print('Submit')
            task_payload['input'] = input.model_dump(by_alias = True)
        if type == suitable_types[1] or type == suitable_types[2]:
            #print('Start or stop')
            task_payload['input'] = {
                'key': key
            }
        
        #print(task_payload)

        task_id = celery_get_id(
            task_name = 'tasks.forwarder-requests',
            task_kwargs = {
                'payload': task_payload
            }
        )
        
        return_dict['output'] = task_id
    return return_dict

@interaction_fastapi.post("/forw/{type}/{user}/{key}")
async def forwarding_interaction(
    request: Request,
    type: str,
    user: str,
    key: str,
    input: Union[Forwarding,dict] = {}
):
    request.app.state.logger.info('Forwarding interaction')

    task_payload = {
        'mode': None,
        'type': None,
        'input': None
    }

    suitable_types = [
        'submit',
        'stop'
    ]

    return_dict = {
        'output': None
    }

    if type in suitable_types:
        task_payload['mode'] = 'forwarding'
        task_payload['type'] = type
        if type == suitable_types[0]:
            #print('submit')
            task_payload['input'] = input.model_dump(by_alias = True)
        if type == suitable_types[1]:
            #print('stop')
            task_payload['input'] = {
                'type': type,
                'user': user,
                'key': key
            }
        
        #print(task_payload)

        task_id = celery_get_id(
            task_name = 'tasks.forwarder-requests',
            task_kwargs = {
                'payload': task_payload
            }
        )
        
        return_dict['output'] = task_id
    return return_dict
    
@interaction_fastapi.get("/arti/{type}/{target}")
async def artifact_interaction(
    request: Request,
    type: str,
    target: str
):  
    request.app.state.logger.info('Artifact interaction')

    task_payload = {
        'mode': None,
        'type': None,
        'input': None
    }

    suitable_types = [
        'logs',
        'sacct',
        'files'
    ]    

    return_dict = {
        'output': None
    }

    if type in suitable_types:
        if type == suitable_types[0]:
            task_payload['mode'] = 'logs'
            if target == 'frontend':
                return_dict['output'] = logger_get_logs(
                    log_path = request.app.state.log_path
                )
            if target == 'backend':
                task_data = celery_await_signature(
                    celery_client = request.app.state.celery,
                    task_name = 'tasks.forwarder-requests',
                    task_kwargs = {
                        'payload': task_payload
                    },
                    timeout = 10
                )
                if task_data['status'] == 'SUCCESS':
                    return_dict['output'] = task_data['result']
        if type == suitable_types[1] or type == suitable_types[2]:
            task_payload['mode'] = 'artifacts'
            task_payload['type'] = type
            task_payload['input'] = {
                'key': target
            }
            
            task_id = celery_get_id(
                task_name = 'tasks.forwarder-requests',
                task_kwargs = {
                    'payload': task_payload
                }
            )
            
            return_dict['output'] = task_id
    return return_dict
