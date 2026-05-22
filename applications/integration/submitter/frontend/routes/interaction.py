from fastapi import APIRouter, Request

from functions.platforms.celery.use import celery_get_id, celery_get_task, celery_await_signature
from functions.platforms.logger.use import logger_get_logs
from typing import Dict

interaction_fastapi = APIRouter(prefix = '/interaction')
 
@interaction_fastapi.get("/task/{type}/{identity}")
async def task_interaction(
    request: Request,
    type: str,
    identity: str,
    input: Dict = {}
):
    # Consider gathering time
    request.app.state.logger.info('Task interaction')
    
    suitable_types = [
        'run',
        'get'
    ]

    return_dict = {
        'task-id': '',
        'task-output': None
    }

    if type in suitable_types:
        if type == suitable_types[0]:
            task_id = celery_get_id(
                task_name = identity,
                task_kwargs = input
            )
            return_dict['task-id'] = task_id
        if type == suitable_types[1]:
            task_data = celery_get_task( 
                celery_client = request.app.state.celery,
                task_id = identity
            )
            return_dict['task-output'] = task_data
    return return_dict
'''
@interaction_fastapi.post("/orch")
async def orchestration_interaction(
    request: Request,
    input: Dict = {}
):
    request.app.state.logger.info('Orchestration interaction')

    task_payload = {
        'mode': 'orch',
        'input': input
    }
    # Might be best to return task id for await
    task_data = celery_await_signature(
        celery_client = request.app.state.celery,
        task_name = 'tasks.submitter-requests',
        task_kwargs = {
            'payload': task_payload
        },
        timeout = 10
    )

    return_dict = {
        'output': None
    }
    if task_data['status'] == 'SUCCESS':
        return_dict['output'] = task_data['result']
    return return_dict 
'''

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
                    task_name = 'tasks.submitter-requests',
                    task_kwargs = {
                        'payload': task_payload
                    },
                    timeout = 10
                )
                if task_data['status'] == 'SUCCESS':
                    return_dict['output'] = task_data['result']
    return return_dict