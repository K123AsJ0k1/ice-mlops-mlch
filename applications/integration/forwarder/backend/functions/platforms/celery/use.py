import time
import os
import shutil

from celery import signature
from celery.result import AsyncResult

def celery_setup_logging():
    log_directory = os.path.abspath('logs')
    
    if os.path.exists(log_directory):
        shutil.rmtree(log_directory)
    
    os.makedirs(log_directory, exist_ok=True)
    log_path = log_directory + '/backend.log'
    with open(log_path, 'w') as f:
        pass

    return log_path

def celery_get_logs(): 
    log_path = os.path.abspath('logs/backend.log')
    listed_logs = {'logs':[]}
    with open(log_path, 'r') as f:
        for line in f:
            listed_logs['logs'].append(line.strip())
    return listed_logs

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

def celery_await_signature(
    celery_client: any,
    task_name: str,
    task_kwargs: any,
    timeout: int
) -> any:
    task = None
    if 0 < len(task_kwargs):
        task = signature(task_name, kwargs = task_kwargs)
    else: 
        task = signature(task_name)
    celery_task = task.apply_async()

    return celery_await_task(
        celery_client = celery_client,
        task_id = celery_task.id,
        timeout = timeout
    )