
def airflow_get_dags(
    airflow_configuration: any,
    limit: int, 
    tags: list,
    order_by: list
) -> any:
    try:
        from airflow_client.client import ApiClient
        from airflow_client.client.api.dag_api import DAGApi
    except ImportError as e:
        raise ImportError("Failed to import", e)

    with ApiClient(airflow_configuration) as api_client:
        api_instance = DAGApi(api_client)
        
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
            print('Airflow get dags error:')
            print(e)
            return {}

def airflow_get_runs(
    airflow_configuration: any,
    dag_id: str,
    limit: int,
    order_by: str
) -> any:
    try:
        from airflow_client.client import ApiClient
        from airflow_client.client.api.dag_run_api import DagRunApi
    except ImportError as e:
        raise ImportError("Failed to import", e)

    with ApiClient(airflow_configuration) as api_client:
        api_instance = DagRunApi(api_client)
        
        try:
            run_list = api_instance.get_dag_runs(
                dag_id = dag_id, 
                limit = limit,
                order_by = order_by
            )

            formated_list = []
            for run in run_list.dag_runs:
                start = run.start_date
                end = run.end_date
                total = 0
                if start and end:
                    total = (end-start).total_seconds()
                    start = start.strftime(f'%f-%S-%M-%H-%d-%m-%Y')
                    end = end.strftime(f'%f-%S-%M-%H-%d-%m-%Y')
                if start is None:
                    start = 0
                if end is None:
                    end = 0

                formated_list.append({
                    'id': run.dag_run_id,
                    'type': run.run_type.value,
                    'state': run.state.value,
                    'start': start,
                    'end': end,
                    'total': total,
                    'trigger': run.triggered_by.value
                })

            return formated_list
        except Exception as e:
            print('Airflow get runs error:')
            print(e)
            return []

def airflow_get_tasks(
    airflow_configuration: any,
    dag_id: str,
    order_by: str
) -> any:
    try:
        from airflow_client.client import ApiClient
        from airflow_client.client.api.task_api import TaskApi
    except ImportError as e:
        raise ImportError("Failed to import", e)

    with ApiClient(airflow_configuration) as api_client:
        api_instance = TaskApi(api_client)
        
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
                    'downstream': task.downstream_task_ids
                })

            return formated_list
        except Exception as e:
            print('Airflow get tasks error')
            print(e)
            return []

def airflow_dag_logs(
    airflow_configuration: any,
    dag_id: str,
    dag_run_id: str,
    task_id: str,
    try_number: int
) -> any:
    try:
        from airflow_client.client import ApiClient
        from airflow_client.client.api.task_instance_api import TaskInstanceApi
    except ImportError as e:
        raise ImportError("Failed to import", e)

    with ApiClient(airflow_configuration) as api_client:
        api_instance = TaskInstanceApi(api_client)
        
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
                        formatted_logs.append(log)
            return formatted_logs
        except Exception as e:
            return []

def airflow_wait_task(
    airflow_configuration: any,
    dag_id: str,
    run_id: str,
    limit: int,
    tries: int,
    timeout: int
) -> bool:
    try:
        import time as t
    except ImportError as e:
        raise ImportError("Failed to import", e)

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

def airflow_trigger_dag(
    airflow_configuration: any,
    dag_id: str,
    parameters: dict
) -> any:
    try:
        from airflow_client.client import ApiClient
        from airflow_client.client.api.dag_run_api import DagRunApi
        from airflow_client.client import TriggerDAGRunPostBody
    except ImportError as e:
        raise ImportError("Failed to import", e)

    with ApiClient(airflow_configuration) as api_client:
        api_instance = DagRunApi(api_client)
        body = TriggerDAGRunPostBody(
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

def airflow_get_metrics(
    airflow_configuration: any,
    dag_limit: int,
    filter_tags: list,
    minimum_tags: int,
    run_limit: int,
) -> any:
    # Works in apache-airflow-client==3.0.2
    airflow_dags = airflow_get_dags(
        airflow_configuration = airflow_configuration,
        limit = dag_limit, 
        tags = filter_tags,
        order_by = 'dag_id'
    )
    
    airflow_metrics = {}
    if 0 < len(airflow_dags):
        for dag_id, dag_metadata in airflow_dags.items():
            dag_tags = dag_metadata['tags']
            found_tags = 0
            for filter_tag in filter_tags:
                if filter_tag in dag_tags:
                    found_tags += 1
            
            dag_metrics = {}
            if minimum_tags <= found_tags:
                dag_runs = airflow_get_runs(
                    airflow_configuration = airflow_configuration,
                    dag_id = dag_id,
                    limit = run_limit,
                    order_by = '-start_date'
                ) 

                if 0 < len(dag_runs):
                    dag_tasks = airflow_get_tasks(
                        airflow_configuration = airflow_configuration,
                        dag_id = dag_id,
                        order_by = 'task_id'
                    )

                    if 0 < len(dag_tasks):
                        downstream_filter = []
                        for dag_task in dag_tasks:
                            downstream = dag_task['downstream']
                            for case in downstream:
                                if not case in downstream_filter:
                                    downstream_filter.append(case)
                            
                        dag_logs = []
                        for dag_run in dag_runs:
                            dag_run_id = dag_run['id']
                            
                            for dag_task in dag_tasks:
                                dag_task_id = dag_task['id']    
                                if not dag_task_id in downstream_filter:
                                    run_logs = airflow_dag_logs(
                                        airflow_configuration = airflow_configuration,
                                        dag_id = dag_id,
                                        dag_run_id = dag_run_id,
                                        task_id = dag_task_id,
                                        try_number = 1
                                    )

                                    if 0 < len(run_logs):
                                        log_key = dag_run_id + '/' + dag_task_id
                                        dag_logs.append({
                                            'id': log_key,
                                            'rows': run_logs
                                        })
                            
                        dag_metrics['runs'] = dag_runs
                        dag_metrics['tasks'] = dag_tasks
                        dag_metrics['logs'] = dag_logs
            airflow_metrics[dag_id] = dag_metrics
    return airflow_metrics