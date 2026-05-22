import copy

def flower_format_tasks(
    tasks: any
) -> any:
    relevant_keys = [
        'worker',
        'children',
        'state',
        'received',
        'started',
        'succeeded',
        'failed',
        'result',
        'timestamp',
        'runtime',
    ]
    # This doesn't gurantee 
    # a time stamp order
    # and it doesn't 
    # specify the children names
    formatted_flower_tasks = {}
    sorted_tasks = sorted(
        tasks.values(), 
        key=lambda x: float(x['received']) if not x['received'] is None else float('-inf')
    )
    for task_info in sorted_tasks:
        if not task_info['name'] is None:
            task_id = task_info['uuid']
            task_name = task_info['name'].split('.')[-1].replace('_','-')
            used_key = ''
            if not task_name in formatted_flower_tasks:
                used_key = '1/' + task_id
                formatted_flower_tasks[task_name] = {
                    used_key: {}
                }
            else:
                new_key = len(formatted_flower_tasks[task_name]) + 1
                new_key = str(new_key)
                used_key = new_key + '/' + task_id
                formatted_flower_tasks[task_name][used_key] = {}
            
            for task_key, task_value in task_info.items():
                if task_key in relevant_keys:
                    formatted_flower_tasks[task_name][task_key] = task_value  
    return formatted_flower_tasks   
'''
def flower_format_executions(
    executions: any 
) -> list:
    execution_table = {
        'name': [],
        'state': [],
        'received': [],
        'timestamp': [],
        'runtime': []
    }
    
    for instance_name, values in executions.items():
        execution_table['name'].append(instance_name)
        execution_table['state'].append(values['state'])
        execution_table['received'].append(values['received'])
        execution_table['timestamp'].append(values['timestamp'])
        execution_table['runtime'].append(round(values['runtime'],5))

    return execution_table
'''