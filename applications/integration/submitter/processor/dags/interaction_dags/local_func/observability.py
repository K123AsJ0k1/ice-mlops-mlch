#import copy
#import re

#import pandas as pd

#from datetime import datetime, timezone, time

#from functions.dict import split_dict_by_length

#from functions.flower.use import flower_get_tasks
#from functions.flower.utility import flower_format_tasks

#from functions.airflow.setup import airflow_setup_configuration
#from functions.airflow.use import airflow_get_metrics
#from functions.airflow.utility import airflow_format_metrics, airflow_format_logs

#from functions.swift.setup import swift_setup_client
#from functions.storage.management import object_storage_interaction, set_object_path

#from functions.utility.pyarrow import pyarrow_serialize_dataframe
# Check imports
def observability_table_path(
    source_type: str,
    case_name: str, 
    start_times: list,
    end_times: list,
    debug_prints: bool
) -> str:
    try:
        from datetime import datetime, timezone
        from icebreaker.storage.management import set_object_path
    except ImportError as e:
        raise ImportError("interaction_dags/local_func/observability failed to import", e)

    table_object_path = None
    if 0 < len(start_times) or 0 < len(end_times):
        # These are in UTC+0
        oldest_time = min(start_times)
        newest_time = max(end_times)

        oldest_dt_object = datetime.fromtimestamp(oldest_time, tz = timezone.utc)
        newest_dt_object = datetime.fromtimestamp(newest_time, tz = timezone.utc)
        
        oldest_year = oldest_dt_object.strftime('year-%Y')
        oldest_month = oldest_dt_object.strftime('month-%m')
        oldest_day = oldest_dt_object.strftime('day-%d')

        oldest_hour = oldest_dt_object.strftime('%H')
        oldest_minute = oldest_dt_object.strftime('%M')
        oldest_second = oldest_dt_object.strftime('%S')

        newest_hour = newest_dt_object.strftime('%H')
        newest_minute = newest_dt_object.strftime('%M')
        newest_second = newest_dt_object.strftime('%S')

        object_name = 'table' 
        object_name += '-' + oldest_hour 
        object_name += '-' + oldest_minute 
        object_name += '-' + oldest_second 
        object_name += '-range'
        object_name += '-' + newest_hour
        object_name += '-' + newest_minute
        object_name += '-' + newest_second
        object_name += '.parquet'

        table_object_path = set_object_path(
            object_name = 'metr',
            path_replacers = {
                'name': source_type
            },
            path_names = [
                case_name,
                oldest_year,
                oldest_month,
                oldest_day,
                object_name
            ],
            debug_prints = debug_prints
        )
    return table_object_path
# Check imports
def observability_table_timerange(
    object_name: str
) -> any:
    try:
        import re
        from datetime import time
    except ImportError as e:
        raise ImportError("interaction_dags/local_func/observability failed to import", e)

    time_match = re.search(r'(\d{2}-\d{2}-\d{2})-range-(\d{2}-\d{2}-\d{2})', object_name)
    timerange = None
    if time_match:
        start_str, end_str = time_match.groups()
        start_t = time(*map(int, start_str.split('-')))
        end_t = time(*map(int, end_str.split('-')))
        timerange = (start_t, end_t)
    return timerange
    
def observability_range_check(
    existing_paths: list, 
    object_path: str
) -> bool:
    object_path_split = object_path.split('.')[0].split('/')

    folder_prefix = '/'.join(object_path_split[:-1])
    new_timerange = observability_table_timerange(
        object_name = object_path_split[-1]
    ) 
    
    relevant_matches = [p for p in existing_paths if p.startswith(folder_prefix)]
    path_exists = False 
    
    if 0 < len(relevant_matches):
        for existing_path in relevant_matches:
            existing_path_split = existing_path.split('.')[0].split('/')
            
            old_timerange = observability_table_timerange(
                object_name = existing_path_split[-1]
            )
            
            new_start, new_end = new_timerange
            old_start, old_end = old_timerange
            if (new_start < old_end) and (old_start < new_end):
                path_exists = True
                
    return path_exists
# Check imports
def observability_table_timestamp(
    source_type: str,
    case_name: str,
    timestamp: int,
    table_name: str,
    debug_prints: bool
) -> str:
    try:
        from datetime import datetime, timezone
        from icebreaker.storage.management import set_object_path
    except ImportError as e:
        raise ImportError("interaction_dags/local_func/observability failed to import", e)

    table_object_path = None
    if 0 < timestamp:
        timestamp_dt_object = datetime.fromtimestamp(timestamp, tz = timezone.utc)
        
        oldest_year = timestamp_dt_object.strftime('year-%Y')
        oldest_month = timestamp_dt_object.strftime('month-%m')
        oldest_day = timestamp_dt_object.strftime('day-%d')

        oldest_hour = timestamp_dt_object.strftime('%H')
        oldest_minute = timestamp_dt_object.strftime('%M')
        oldest_second = timestamp_dt_object.strftime('%S')
        oldest_microsecond = timestamp_dt_object.strftime('%f')

        object_name = 'table-' + table_name
        object_name += '-' + oldest_hour 
        object_name += '-' + oldest_minute 
        object_name += '-' + oldest_second 
        object_name += '-' + oldest_microsecond
        object_name += '.parquet'

        table_object_path = set_object_path(
            object_name = 'metr',
            path_replacers = {
                'name': source_type
            },
            path_names = [
                case_name,
                oldest_year,
                oldest_month,
                oldest_day,
                object_name
            ],
            debug_prints = debug_prints
        )
    return table_object_path
# Check imports
def observability_flower_interaction(
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
                    table_object_path = observability_table_path(
                        source_type = 'flower-task',
                        case_name = task_name, 
                        start_times = table['received'],
                        end_times = table['timestamp'],
                        debug_prints = False
                    )
                    
                    table_exists = observability_range_check(
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

def observability_airflow_interaction(
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
                        table_object_path = observability_table_path(
                            source_type = 'airflow-dag-metrics',
                            case_name = dag_id, 
                            start_times = table['start'],
                            end_times = table['end'],
                            debug_prints = False
                        )
                        
                        table_exists = observability_range_check(
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
                    table_object_path = observability_table_timestamp(
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

def observability_submitter_interaction(
    swift_parameters: any,
    bucket_parameters: any,
    storage_parameters: any  
) -> any:  
    try:
        from icebreaker.swift.setup import swift_setup_client
        from icebreaker.storage.management import object_storage_interaction
    except ImportError as e:
        raise ImportError("interaction_dags/local_func/observability failed to import", e)

    print('Observability submitter interaction')
    # This uses apache-airflow-client==3.0.2
    # Updating will create changes, which show as validation errors
    # BE AWARE THAT ALL TIME IS IN UTC AND AIRFLOW UI SHOWS UTC+2 CORRECTED TIMES
    data_stored = False
    
    swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )
    # We might also need to save fastapi and celery logs
    bucket_target = bucket_parameters['target']
    bucket_prefix = bucket_parameters['prefix']
    bucket_user = bucket_parameters['user']
    debug_prints = storage_parameters['debug-prints']

    object_list = object_storage_interaction(
        storage_client = swift_client,
        lock_parameters = storage_parameters['lock'],
        lock_location = storage_parameters['airflow-lock-location'],
        parameters = {
            'mode': 'list',
            'bucket-target': bucket_target,
            'bucket-prefix': bucket_prefix,
            'bucket-user': bucket_user,
            'debug-prints': debug_prints,
            'object-name': 'metr',
            'path-replacers': {
                'name': 'time-path'
            },
            'path-names': [],
            'overwrite': False
        },
        object_data = None,
        object_metadata = None 
    )

    data_stored = observability_flower_interaction(
        swift_client = swift_client,
        bucket_parameters = bucket_parameters,
        storage_parameters = storage_parameters,
        object_list = object_list
    )
    
    data_stored = observability_airflow_interaction(
        swift_client = swift_client,
        bucket_parameters = bucket_parameters,
        storage_parameters = storage_parameters,
        object_list = object_list
    )

    return data_stored