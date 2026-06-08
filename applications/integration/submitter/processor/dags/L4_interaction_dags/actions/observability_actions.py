# check imports and function inputs
def observability_action_flower_interaction(
    swift_client: any,
    bucket_parameters: any,
    storage_parameters: any,
    object_list: any
):
    try:
        import pandas as pd
        from icebreaker.flower.use import flower_get_tasks
        from icebreaker.flower.utility import flower_format_tasks
        from icebreaker.pyarrow.use import pyarrow_serialize_dataframe
        from L4_interaction_dags.utility.observability_utility import observability_utility_table_path, observability_utility_range_check
    except ImportError as e:
        raise ImportError("interaction_dags/local_func/observability failed to import", e)

    print('Observability flower interaction')
    data_stored = False
    
    flower_configuration = storage_parameters['flower-configuration']
    debug_prints = storage_parameters['debug-prints']
    flower_observability = storage_parameters['observability']['flower']

    bucket_target = bucket_parameters['target']
    bucket_prefix = bucket_parameters['prefix']
    bucket_user = bucket_parameters['user']

    flower_tasks = flower_get_tasks(
        flower_address = flower_configuration['address'],
        flower_port = flower_configuration['port'],
        flower_username = flower_configuration['username'],
        flower_password = flower_configuration['password'],
    )
    task_amount = len(flower_tasks)
    print('Flower tasks amount: ' + str(task_amount))
    if 0 < task_amount:
        formatted_flower_tasks = flower_format_tasks(
            tasks = flower_tasks
        )
        
        task_min_rows = flower_observability['task-table-min-rows']
        task_max_rows = flower_observability['task-table-max-rows']
        print('Table row min-max: ' + str(task_min_rows) + '-' + str(task_max_rows))
        print('Amount of tasks: ' + str(len(formatted_flower_tasks)))
        for task_name, executions in formatted_flower_tasks.items():
            '''
            print('Task name: ' + str(task_name))
            table_template = {
                'name': [],
                'state': [],
                'received': [],
                'timestamp': [],
                'runtime': []
            }
            table_index = 0
            table_rows = 0
            flower_tables = [copy.deepcopy(table_template)]
            # This needs to separate tables based on year, month and day
            for instance_name, values in executions.items():
                received = values['received']
                timestamp = values['timestamp']
                if task_max_rows <= table_rows:
                    flower_tables.append(copy.deepcopy(table_template))
                    table_index += 1
                    table_rows = 0
                flower_tables[table_index]['name'].append(instance_name)
                flower_tables[table_index]['state'].append(values['state'])
                flower_tables[table_index]['received'].append(received)
                flower_tables[table_index]['timestamp'].append(timestamp)
                flower_tables[table_index]['runtime'].append(round(values['runtime'],5))
                table_rows += 1
            '''
            
            #amount_of_tables = len(flower_tables)
            #print('Amount of produced tables: ' + str(amount_of_tables))
            #if 0 < amount_of_tables:
            flower_tables = []
            tables_stored = 0
            for table in flower_tables:
                table_rows = len(table['name'])
                if task_min_rows <= table_rows:
                    table_object_path = observability_utility_table_path(
                        source_type = 'flower-task',
                        case_name = task_name, 
                        start_times = table['received'],
                        end_times = table['timestamp'],
                        debug_prints = False
                    )
                    
                    table_exists = observability_utility_range_check(
                        existing_paths = object_list.keys(), 
                        object_path = table_object_path
                    )
                    
                    if not table_exists:    
                        data_df = pd.DataFrame.from_dict(table)
                        
                        stored_data = pyarrow_serialize_dataframe(
                            dataframe = data_df
                        )

                        stored_metadata = {'version': 1}
                        object_path_split = table_object_path.split('/')
                        '''
                        data_stored = object_storage_interaction(
                            storage_client = swift_client,
                            lock_parameters = storage_parameters['lock'],
                            lock_location = storage_parameters['airflow-lock-location'],
                            parameters = {
                                'mode': 'send',
                                'bucket-target': bucket_target,
                                'bucket-prefix': bucket_prefix,
                                'bucket-user': bucket_user,
                                'debug-prints': debug_prints,
                                'object-name': 'metr',
                                'path-replacers': {
                                    'name': object_path_split[1]
                                },
                                'path-names': object_path_split[2:],
                                'overwrite': True
                            },
                            object_data = stored_data,
                            object_metadata = stored_metadata
                        )
                        '''
                        tables_stored += 1
            print('Task tables stored: ' + str(tables_stored))
    return data_stored

def observability_action_airflow_interaction(
    swift_client: any,
    bucket_parameters: any,
    storage_parameters: any,
    object_list: any
):
    try:
        import pandas as pd
        from icebreaker.pyarrow.use import pyarrow_serialize_dataframe
        from icebreaker.airflow.setup import airflow_setup_configuration
        from icebreaker.airflow.use import airflow_get_metrics
        from icebreaker.airflow.utility import airflow_format_metrics, airflow_format_logs
        from icebreaker.misc.dict import split_dict_by_length
        from L4_interaction_dags.utility.observability_utility import observability_utility_table_path, observability_utility_range_check, observability_utility_table_timestamp
    except ImportError as e:
        raise ImportError("interaction_dags/local_func/observability failed to import", e)

    print('Observability airflow interaction')
    data_stored = False

    airflow_configuration = storage_parameters['airflow-configuration']
    debug_prints = storage_parameters['debug-prints']
    airflow_observability = storage_parameters['observability']['airflow']

    bucket_target = bucket_parameters['target']
    bucket_prefix = bucket_parameters['prefix']
    bucket_user = bucket_parameters['user']

    airflow_config = airflow_setup_configuration(
        airflow_host = airflow_configuration['host'],
        airflow_username = airflow_configuration['username'],
        airflow_password = airflow_configuration['password']
    )
    
    if not airflow_config.access_token is None:
        airflow_metrics = airflow_get_metrics(
            airflow_configuration = airflow_config,
            dag_limit = airflow_observability['dag-limit'],
            filter_tags = airflow_observability['filter-tags'],
            minimum_tags = airflow_observability['minimum-tags'],
            run_limit = airflow_observability['run-limit']
        )
        metrics_amount = len(airflow_metrics)
        print('Airflow metrics amount: ' + str(metrics_amount))
        if 0 < metrics_amount:
            formatted_airflow_metrics = airflow_format_metrics(
                metrics = airflow_metrics,
                wanted_dags = airflow_observability['metrics-wanted-dags']
            )

            print('Amount of metric DAGs: ' + str(len(formatted_airflow_metrics)))

            formatted_airflow_logs = airflow_format_logs(
                metrics = airflow_metrics,
                wanted_dags = airflow_observability['logs-wanted-dags']
            )

            print('Amount of log DAGs: ' + str(len(formatted_airflow_logs)))

            metrics_min_rows = airflow_observability['metrics-table-min-rows']
            metrics_max_rows = airflow_observability['metrics-table-max-rows']
            print('Metrics table row min-max: ' + str(metrics_min_rows) + '-' + str(metrics_max_rows))
            tables_stored = 0
            for dag_id, metrics in formatted_airflow_metrics.items():
                #print('DAG name: ' + str(dag_id))
                # This needs to separate tables based on year, month and day
                airflow_metric_tables = list(split_dict_by_length(
                    dict_lists = metrics,
                    list_length = metrics_max_rows
                ))
                # Be aware that this way makes tables have different months and days
                # with the location being the oldest timestamp
                # while the newest time stamp is what ever new day regardless of month and day
                # It might be in the future required to separate tables by day
                for table in airflow_metric_tables: 
                    table_rows = len(table['id'])
                    if metrics_min_rows <= table_rows:
                        table_object_path = observability_utility_table_path(
                            source_type = 'airflow-dag-metrics',
                            case_name = dag_id, 
                            start_times = table['start'],
                            end_times = table['end'],
                            debug_prints = False
                        )
                        
                        table_exists = observability_utility_range_check(
                            existing_paths = object_list.keys(), 
                            object_path = table_object_path
                        )

                        if not table_exists: 
                            data_df = pd.DataFrame.from_dict(table)
                            
                            stored_data = pyarrow_serialize_dataframe(
                                dataframe = data_df
                            )

                            stored_metadata = {'version': 1}
                            object_path_split = table_object_path.split('/')
                            '''
                            data_stored = object_storage_interaction(
                                storage_client = swift_client,
                                lock_parameters = storage_parameters['lock'],
                                lock_location = storage_parameters['airflow-lock-location'],
                                parameters = {
                                    'mode': 'send',
                                    'bucket-target': bucket_target,
                                    'bucket-prefix': bucket_prefix,
                                    'bucket-user': bucket_user,
                                    'debug-prints': debug_prints,
                                    'object-name': 'metr',
                                    'path-replacers': {
                                        'name': object_path_split[1]
                                    },
                                    'path-names': object_path_split[2:],
                                    'overwrite': True
                                },
                                object_data = stored_data,
                                object_metadata = stored_metadata
                            )
                            '''
                            tables_stored += 1
            print('Metrics tables stored: ' + str(tables_stored))
            tables_stored = 0
            for dag_id, logs in formatted_airflow_logs.items():
                for values in logs:
                    log_activation = values['activation']
                    log_timestamp = values['timestamp']
                    log_task = values['task']
                    log_rows = values['rows']
                    
                    table_name = log_activation + '-' + log_task
                    table_object_path = observability_utility_table_timestamp(
                        source_type = 'airflow-dag-logs',
                        case_name = dag_id,
                        timestamp = log_timestamp,
                        table_name = table_name,
                        debug_prints = False
                    )

                    table_exists = False
                    for existing_path in object_list.keys():
                        if existing_path == table_object_path:
                            table_exists = True

                    if not table_exists: 
                        data_df = pd.DataFrame.from_dict({
                            'rows': log_rows
                        })
                        
                        stored_data = pyarrow_serialize_dataframe(
                            dataframe = data_df
                        )

                        stored_metadata = {'version': 1}
                        object_path_split = table_object_path.split('/')
                        '''
                        data_stored = object_storage_interaction(
                            storage_client = swift_client,
                            lock_parameters = storage_parameters['lock'],
                            lock_location = storage_parameters['airflow-lock-location'],
                            parameters = {
                                'mode': 'send',
                                'bucket-target': bucket_target,
                                'bucket-prefix': bucket_prefix,
                                'bucket-user': bucket_user,
                                'debug-prints': debug_prints,
                                'object-name': 'metr',
                                'path-replacers': {
                                    'name': object_path_split[1]
                                },
                                'path-names': object_path_split[2:],
                                'overwrite': True
                            },
                            object_data = stored_data,
                            object_metadata = stored_metadata
                        )
                        '''
                        tables_stored += 1
            print('Log tables stored: ' + str(tables_stored))
    return data_stored