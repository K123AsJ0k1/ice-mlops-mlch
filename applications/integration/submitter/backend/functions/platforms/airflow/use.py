import airflow_client.client
import time as t

def airflow_get_dags(
    airflow_configuration: any,
    limit: int, 
    tags: list,
    order_by: str
) -> any:
    with airflow_client.client.ApiClient(airflow_configuration) as api_client:
        api_instance = airflow_client.client.DAGApi(api_client)
        
        try:
            dag_list = api_instance.get_dags(
                limit = limit,
                tags = tags,
                order_by = order_by
            )

            formated_list = {}
            for dag in dag_list.dags:
                dag_id = dag.dag_id
                dag_tags = []
                for tag in dag.tags:
                    dag_tags.append(tag.name)
                formated_list[dag_id] = {
                    'tags': dag_tags
                }

            return formated_list
        except Exception as e:
            return {}

def airflow_get_runs(
    airflow_configuration: any,
    dag_id: str,
    limit: int,
    order_by: str
) -> any:
    with airflow_client.client.ApiClient(airflow_configuration) as api_client:
        api_instance = airflow_client.client.DagRunApi(api_client)
        
        try:
            run_list = api_instance.get_dag_runs(
                dag_id = dag_id, 
                limit = limit,
                order_by = order_by
            )

            formated_list = []
            for run in run_list.dag_runs:
                time = (run.end_date-run.start_date).total_seconds()
                formated_list.append({
                    'id': run.dag_run_id,
                    'type': run.run_type.value,
                    'state': run.state.value,
                    'start': run.start_date.strftime(f'%f-%S-%M-%H-%d-%m-%Y'),
                    'end': run.end_date.strftime(f'%f-%S-%M-%H-%d-%m-%Y'),
                    'time': time,
                    'trigger': run.triggered_by.value
                })

            return formated_list
        except Exception as e:
            return {}

def airflow_get_tasks(
    airflow_configuration: any,
    dag_id: str,
    order_by: str
) -> any:
    with airflow_client.client.ApiClient(airflow_configuration) as api_client:
        api_instance = airflow_client.client.TaskApi(api_client)
        
        try:
            task_list = api_instance.get_tasks(
                dag_id = dag_id, 
                order_by = order_by
            )
            
            formated_list = []
            for task in task_list.tasks:
                formated_parameters = {}
                for key in task.params.keys():
                    formated_parameters[key] = task.params[key]['value']
                    
                formated_list.append({
                    'id': task.task_id,
                    'name': task.task_display_name,
                    'parameters': formated_parameters,
                    'downstream': task.downstream_task_ids
                })

            return formated_list
        except Exception as e:
            return {}

def airflow_trigger_dag(
    airflow_configuration: any,
    dag_id: str,
    parameters: dict
) -> any:
    with airflow_client.client.ApiClient(airflow_configuration) as api_client:
        api_instance = airflow_client.client.DagRunApi(api_client)
        body = airflow_client.client.TriggerDAGRunPostBody(
            conf = parameters
        ) 
        
        try:
            triggered_dag = api_instance.trigger_dag_run(
                dag_id = dag_id, 
                trigger_dag_run_post_body = body
            )
            
            formated_dag = {
                'id': triggered_dag.dag_run_id,
                'parameters': triggered_dag.conf,
                'state': triggered_dag.state.value,
                'queue': triggered_dag.queued_at.strftime(f'%f-%S-%M-%H-%d-%m-%Y'),
                'after': triggered_dag.run_after.strftime(f'%f-%S-%M-%H-%d-%m-%Y')
            }

            return formated_dag
        except Exception as e:
            return {}
      
def airflow_dag_logs(
    airflow_configuration: any,
    dag_id: str,
    dag_run_id: str,
    task_id: str,
    try_number: int,
    filtered_words: any
) -> any:
    with airflow_client.client.ApiClient(airflow_configuration) as api_client:
        api_instance = airflow_client.client.TaskInstanceApi(api_client)
        
        try:
            task_logs = api_instance.get_log(
                dag_id = dag_id, 
                dag_run_id = dag_run_id, 
                task_id = task_id, 
                try_number = try_number
            )
            
            formatted_logs = []
            for tuple_value in task_logs.content:
                if tuple_value[0] == 'actual_instance':
                    for row in tuple_value[1]:
                        log = row.event
                        first_character = log[0]
                        if first_character.isalpha():
                            if not any(word in log for word in filtered_words):
                                formatted_logs.append(log)
            return formatted_logs
        except Exception as e:
            return {}
        
def airflow_wait_task(
    airflow_configuration: any,
    dag_id: str,
    run_id: str,
    limit: int,
    tries: int,
    timeout: int
) -> bool:
    success = False
    for i in range(tries):
        runs = airflow_get_runs(
            airflow_configuration = airflow_configuration,
            dag_id = dag_id,
            limit = limit,
            order_by = '-start_date'
        )
        stop = False
        for case in runs:
            case_id = case['id']
            case_state = case['state']
            if case_id == run_id:
                if case_state == 'success' or case_state == 'failed':
                    if case_state == 'success':
                        success = True
                    stop = True
                    break
        if stop:
            break
        t.sleep(timeout)
    return success