import time

from celery import signature
from celery.result import AsyncResult

def celery_get_task( 
    celery_client: any,
    task_id: str
) -> any:
    task_data = {
        'status': '',
        'result': None
    }
    
    response = AsyncResult(
        id = task_id, 
        app = celery_client
    )
    task_state = response.state

    task_data['status'] = task_state 
    if task_state == 'SUCCESS':
        response = AsyncResult(
            id = task_id, 
            app = celery_client
        )
        
        task_data['result'] = response.result
    return task_data

def celery_await_task(
    celery_client: any,
    task_id: str,
    timeout: int
) -> any:
    task_data = {}
    start = time.time()
    # In the case of 
    # errors this
    # makes wait the 
    # whole timeout
    while time.time() - start <= timeout:
        task_data = celery_get_task(
            celery_client = celery_client,
            task_id = task_id
        )
        if not task_data['result'] is None:
            break
        time.sleep(2)
    return task_data

def celery_get_id(
    task_name: str,
    task_kwargs: any
) -> str:
    task = None
    if 0 < len(task_kwargs):
        task = signature(task_name, kwargs = task_kwargs)
    else: 
        task = signature(task_name)
    celery_task = task.apply_async()
    return celery_task.id

def celery_await_signature(
    celery_client: any,
    task_name: str,
    task_kwargs: any,
    timeout: int
) -> any:
    task_id = celery_get_id(
        task_name = task_name,
        task_kwargs = task_kwargs
    )

    return celery_await_task(
        celery_client = celery_client,
        task_id = task_id,
        timeout = timeout
    )