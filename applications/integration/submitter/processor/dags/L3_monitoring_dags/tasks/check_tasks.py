# Works for halted, check when cancelling 
def check_task_platform_interaction(
    swift_parameters: any,
    bucket_parameters: any,
    storage_parameters: any,
    platfrom_parameters: any   
) -> any: 
    try:
        import copy
        import time as t
        import pickle
        from functions.utility.airflow import airflow_check_connection
        from icebreaker.misc.dict import create_nested_dict, update_dict_value
        from L3_monitoring_dags.utility.check_utility import check_utility_platform_commands
        from functions.actions.monitor_actions import monitor_action_check_jobs
        from L3_monitoring_dags.actions.check_actions import check_action_cancel_job
        from icebreaker.swift.setup import swift_setup_client
        from icebreaker.misc.dict import get_dict_value
        from icebreaker.storage.management import object_storage_interaction
    except ImportError as e:
        raise ImportError("L3_orchestration_dags/tasks/fill_tasks failed to import", e) 

    storage_dag_inputs = []
    platform_name = platfrom_parameters['name']
    target_platform = 'hpc-' + platform_name
    connection_exists = airflow_check_connection(
        connection_id = target_platform
    )
    print('Checking connections for ' + str(target_platform))
    if connection_exists:
        platform_setup_objects = platfrom_parameters['object-names']['check']
        print('Checking amount of objects ' + str(len(platform_setup_objects)))
        if 0 < len(platform_setup_objects):
            check_commands = check_utility_platform_commands(
                target_platform = target_platform
            )
            if 0 < len(check_commands):
                swift_client = swift_setup_client(
                    swift_parameters = swift_parameters
                )
                bucket_target = bucket_parameters['target']
                bucket_prefix = bucket_parameters['prefix']
                bucket_user = bucket_parameters['user']
                debug_prints = storage_parameters['debug-prints']
                
                platform_monitoring = False
                platform_halted = False
                interaction_timeout = False
                time_name = 'submitter-trigger|beat|celery|airflow|submitter-monitoring-sequence|submitter-check-operation'
                for object_name in platform_setup_objects:
                    platform_start_time = t.time()
                    orch_object = object_storage_interaction(
                        storage_client = swift_client,
                        lock_parameters = storage_parameters['lock'],
                        lock_location = storage_parameters['airflow-lock-location'],
                        parameters = {
                            'mode': 'get',
                            'bucket-target': bucket_target,
                            'bucket-prefix': bucket_prefix,
                            'bucket-user': bucket_user,
                            'debug-prints': debug_prints,
                            'object-name': 'mana',
                            'path-replacers': {
                                'name': object_name
                            },
                            'path-names': [],
                            'overwrite': False
                        },
                        object_data = None,
                        object_metadata = None
                    )
                    orch_data = pickle.loads(orch_object[0])
                    
                    platform_path = 'platforms-' + platform_name
                    state_path = platform_path + '-state'
                    order_states_path = state_path + '-order'
                    jobs_path = platform_path+ '-jobs'

                    order_states = get_dict_value(
                        target_dict = orch_data,
                        key_path = order_states_path,
                        separator = '-'
                    )

                    jobs = get_dict_value(
                        target_dict = orch_data,
                        key_path = jobs_path,
                        separator = '-'
                    )

                    update_dict = create_nested_dict(
                        target_dict = {},
                        key_path = jobs_path,
                        separator = '-'
                    ) 
                    
                    if interaction_timeout:
                        t.sleep(2)
                    
                    current_jobs = monitor_action_check_jobs(
                        storage_parameters = storage_parameters,
                        lock_location = storage_parameters['airflow-lock-location'],
                        target_platform = target_platform,
                        commands = check_commands 
                    )
                    print(update_dict)
                    update_list = []
                    job_times = []
                    for job in jobs:
                        job_start_time = t.time()
                        job_id = job['id']
                        job_status = job['status']
                        job_states = job_status['states']
                        job_order = job_status['order']
                        print('Checking job: ', job_id)
                        
                        modified_status = {}
                        job_exists = False
                        if 'jobid' in current_jobs:
                            interaction_timeout = True
                            if 0 < len(current_jobs['jobid']):
                                index = 0
                                job_exists = False
                                for case in current_jobs['jobid']:
                                    if job_id == case:
                                        job_exists = True
                                        if order_states['stop'] or job_order['stop']:
                                            print('Stopping running job')
                                            checked_jobs = check_action_cancel_job(
                                                storage_parameters = storage_parameters,
                                                lock_location = storage_parameters['airflow-lock-location'],
                                                target_platform = target_platform,
                                                commands = check_commands,
                                                job_id = job_id
                                            )

                                            if 'state' in checked_jobs:
                                                job_states.append(checked_jobs['state'][index])

                                            modified_status['interaction'] = {'stopped': True}
                                            modified_status['submitter'] = {'halted': True}
                                            platform_halted = True
                                        else:
                                            print('Monitoring running job')
                                            platform_monitoring = True
                                            modified_status['submitter'] = {'monitoring': True}
                                        pass
                                    index += 1
                                
                        if not job_exists:
                            print('Job has exited')
                            platform_halted = True
                            modified_status['submitter'] = {'halted': True}

                        update_list.append({
                            'id': job_id,
                            'status': modified_status
                        })

                        job_end_time = t.time()
                        job_times.append(
                            {
                                'name': time_name,
                                'start': job_start_time,
                                'end': job_end_time
                            }
                        )

                if 0 < len(update_list):
                    update_dict_value(
                        target_dict = update_dict,
                        key_path = jobs_path,
                        separator = '-',
                        new_value = update_list
                    )
                    print(update_dict)
                    update_dict_value(
                        target_dict = update_dict,
                        key_path = state_path,
                        separator = '-',
                        new_value = {
                            'interaction': {
                                'complete': platform_halted
                            },
                            'submitter': {
                                'monitoring': platform_monitoring,
                                'halted': platform_halted
                            }
                        }
                    )
                    print(update_dict)
                    modified_storage_parameters = copy.deepcopy(storage_parameters)
                    modified_storage_parameters['object-key'] = object_name.split('.')[0]
                    modified_storage_parameters['object-input'] = update_dict

                    if 'general-time' in modified_storage_parameters:
                        modified_storage_parameters['general-time']['name'] = modified_storage_parameters['general-time']['name'] + '|submitter-check-operation'

                    modified_storage_parameters['job-time'] = {
                        'target': platform_name,
                        'times': job_times
                    }

                    platform_end_time = t.time()
                    modified_storage_parameters['platform-time'] = {
                        'target': platform_name,
                        'name': time_name,
                        'start': platform_start_time, 
                        'end': platform_end_time
                    }

                    expand_input = {
                        'trigger_dag_id': 'submitter-storage-interaction',
                        'conf': {
                            'swift-parameters': swift_parameters,
                            'bucket-parameters': bucket_parameters,
                            'storage-parameters': modified_storage_parameters
                        }
                    }
                    storage_dag_inputs.append(expand_input)    
    return storage_dag_inputs