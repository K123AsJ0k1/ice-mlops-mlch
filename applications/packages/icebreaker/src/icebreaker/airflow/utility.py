
def airflow_cli_connections(
    secret_dict: any
): 
    try:
        import json
    except ImportError as e:
        raise ImportError("Failed to import", e)

    secret_platforms = secret_dict['platforms']
    secret_connections = secret_dict['connections']
    
    airflow_connections = []
    for p_type, values in secret_platforms.items():
        for name, parameters  in values.items():
            connection_type = parameters['type']
            if connection_type == 'ssh':
                connection_host = parameters['address']
                connection_user = parameters['user']
                connection_key = parameters['key']
                key_parameters = secret_connections[connection_type][connection_key]
                connection_path = key_parameters['path']
                connection_phrase = key_parameters['phrase']
                connection_id = p_type + '-' + name
    
                values = {
                    'conn_type': 'ssh',
                    'login': connection_user,
                    'password': connection_phrase,
                    'host': connection_host,
                    'port': 22,
                    'extra': {
                        'key_file': connection_path
                    }
                }
    
                compose_command = "-f " + os.path.abspath('applications/airflow/docker-compose.yaml')
                connection_name = "'" + connection_id + "'"
                connection_json = "'" + json.dumps(values) + "'"
                cli_command = [
                    "docker", 
                    "compose", 
                    compose_command,
                    "run", 
                    "airflow-worker",
                    "airflow", 
                    "connections", 
                    "add",
                    connection_name,
                    "--conn-json",
                    connection_json
                ]
            
                airflow_connections.append(' '.join(cli_command))
    return airflow_connections

def airflow_format_metrics(
    metrics: any,
    wanted_dags: list
) -> any:
    try:
        import copy
        from .misc.general import get_unix_time
    except ImportError as e:
        raise ImportError("Failed to import", e)

    formatted_airflow_metrics = {}

    metrics_template = {
        'id': [],
        'task': [],
        'downstream': [],
        'state': [],
        'start': [],
        'end': [],
        'total': [],
        'trigger': []
    }

    valid_states = [
        'success',
        'failed'
    ]

    for dag_id in metrics.keys():
        if dag_id in wanted_dags:
            dag_metrics = copy.deepcopy(metrics_template)

            dag_data = metrics[dag_id] 
            added = False
            if 'runs' in dag_data:
                dag_runs = dag_data['runs']
                dag_tasks = dag_data['tasks']
                
                main_task = 'null'
                downstream_tasks = 'null'
                if 0 < len(dag_tasks):
                    main_task = dag_tasks[0]['id']
                    downstream_tasks = '|'.join(dag_tasks[0]['downstream'])

                for run in dag_runs:
                    run_state = run['state']
                    if run_state in valid_states:
                        start_time = get_unix_time(
                            time = run['start'],
                            separator = '-',
                            largest_first = False
                        )
                        
                        end_time = get_unix_time(
                            time = run['end'],
                            separator = '-',
                            largest_first = False
                        )
                    
                        dag_metrics['id'].append(run['id'])
                        dag_metrics['task'].append(main_task)
                        dag_metrics['downstream'].append(downstream_tasks)
                        dag_metrics['state'].append(run_state)
                        dag_metrics['start'].append(start_time)
                        dag_metrics['end'].append(end_time)
                        dag_metrics['total'].append(run['total'])
                        dag_metrics['trigger'].append(run['trigger'])
                        added = True  
            if added:
                formatted_airflow_metrics[dag_id] = dag_metrics
    return formatted_airflow_metrics
        
def airflow_format_logs(
    metrics: any,
    wanted_dags: list
) -> any:
    try:
        import copy
        from .misc.general import get_unix_time
    except ImportError as e:
        raise ImportError("Failed to import", e)

    formatted_airflow_logs = {}

    logs_template = {
        'activation': '',
        'timestamp': '',
        'task': '',
        'rows': []
    }

    for dag_id in metrics.keys():
        if dag_id in wanted_dags:
            dag_data = metrics[dag_id] 
            added = False
            data_list = []
            if 'logs' in dag_data:
                dag_logs = dag_data['logs']
                for values in dag_logs:
                    if 'id' in values:
                        log_id = values['id']
                        id_split = log_id.split('/')
                        run_id = id_split[0].split('__')
                        activation_type = run_id[0]
                        activation_time = run_id[-1].split('+')[0]
                        activation_time = activation_time.replace('T', '-')
                        activation_time = activation_time.replace(':', '-')
                        activation_time = activation_time.replace('.', '-')

                        timestamp = get_unix_time(
                            time = activation_time,
                            separator = '-',
                            largest_first = True
                        )
                        
                        log_task = id_split[-1]
                        
                        log_data = copy.deepcopy(logs_template)
                        log_data['activation'] = activation_type
                        log_data['timestamp'] = timestamp
                        log_data['task'] = log_task.replace('_','-')
                        log_data['rows'] = values['rows']
                        data_list.append(log_data)
                        added = True
            if added:
                formatted_airflow_logs[dag_id] = data_list
    return formatted_airflow_logs