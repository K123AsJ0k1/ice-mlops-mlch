
# check imports and function inputs
def run_platform_interaction(
    swift_parameters: any,
    bucket_parameters: any,
    storage_parameters: any,
    platfrom_parameters: any
) -> any:
    try:
        #import copy
        #import time as t
        #from global_functions.utility.airflow import airflow_check_connection
        #from icebreaker.misc.dict import create_nested_dict, update_dict_value

        #import pickle
        #import copy

        #from functions.dict import get_dict_value, create_nested_dict, update_dict_value

        #from functions.utility.misc import base_check_connection
        #from functions.utility.platform import platform_run_commands

        #from functions.swift.setup import swift_setup_client
        #from functions.storage.management import object_storage_interaction

        #from functions.actions.run import run_submit_job
        #from functions.actions.monitor import monitor_check_jobs
        import time as t
        import pickle
        import copy
        
        from functions.utility.airflow import airflow_check_connection
        from L3_orchestration_dags.utility.run_utility import run_utility_platform_commands
        from icebreaker.swift.setup import swift_setup_client
        from icebreaker.storage.management import object_storage_interaction
        from icebreaker.misc.dict import get_dict_value, create_nested_dict, update_dict_value
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
        platform_setup_objects = platfrom_parameters['object-names']['run']
        print('Checking amount of objects ' + str(len(platform_setup_objects)))
        if 0 < len(platform_setup_objects):
            run_commands = run_utility_platform_commands(
                target_platform = target_platform
            )
            if 0 < len(run_commands):
                swift_client = swift_setup_client(
                    swift_parameters = swift_parameters
                )
                bucket_target = bucket_parameters['target']
                bucket_prefix = bucket_parameters['prefix']
                bucket_user = bucket_parameters['user']
                debug_prints = storage_parameters['debug-prints']

                time_name = 'submitter-trigger|beat|celery|airflow|submitter-interaction-sequence|submitter-run-operation'
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

                    platforms_path = 'platforms-' + platform_name
                    properties_workspaces_path = platforms_path + '-properties-workspaces'
                    jobs_path = platforms_path + '-jobs'
                    interaction_path = platforms_path + '-state-interaction'

                    workspaces = get_dict_value(
                        target_dict = orch_data,
                        key_path = properties_workspaces_path,
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

                    update_dict = create_nested_dict(
                        target_dict = update_dict,
                        key_path = interaction_path,
                        separator = '-'
                    ) 

                    update_list = []
                    job_times = []
                    for job in jobs:
                        job_start_time = t.time()
                        job_path = job['path']
                        job_path_split = job_path.split('/')
                        job_directory = '/'.join(job_path_split[:-1])
                        print('Checking job file: ', job_path)
                        for workspace in workspaces:
                            workspace_path = workspace['path']
                            if workspace_path == job_directory:
                                job_status = job['status']
                                job_order = job_status['order']
                                job_interaction = job_status['interaction']
                                if job_order['start']:
                                    if not job_interaction['submitted']:
                                        job_id = run_submit_job(
                                            storage_parameters = storage_parameters,
                                            lock_location = storage_parameters['airflow-lock-location'],
                                            target_platform = target_platform,
                                            commands = run_commands,
                                            file_path = job_path
                                        )
                                        
                                        t.sleep(2)

                                        current_jobs = monitor_check_jobs(
                                            storage_parameters = storage_parameters,
                                            lock_location = storage_parameters['airflow-lock-location'],
                                            target_platform = target_platform,
                                            commands = run_commands
                                        )
                                    
                                        if 'jobid' in current_jobs:
                                            if 0 < len(current_jobs['jobid']):
                                                index = 0
                                                for case in current_jobs['jobid']:
                                                    if job_id == case:
                                                        update_list.append({
                                                            'id': job_id,
                                                            'status': {
                                                                'states': [current_jobs['state'][index]],
                                                                'interaction': {'submitted': True},
                                                                'submitter': {'operating': True}
                                                            }
                                                        })
                                                        job_end_time = t.time()
                                                        job_times.append(
                                                            {
                                                                'name': time_name,
                                                                'start': job_start_time,
                                                                'end': job_end_time
                                                            }
                                                        )
                                                        break
                                                    index += 1
                    if 0 < len(update_list):
                        update_dict_value(
                            target_dict = update_dict,
                            key_path = jobs_path,
                            separator = '-',
                            new_value = update_list
                        )

                        update_dict_value(
                            target_dict = update_dict,
                            key_path = interaction_path,
                            separator = '-',
                            new_value = {
                                'running': True
                            }
                        )
                        print(update_dict)
                        modified_storage_parameters = copy.deepcopy(storage_parameters)
                        modified_storage_parameters['object-key'] = object_name.split('.')[0]
                        modified_storage_parameters['object-input'] = update_dict
                        
                        if 'general-time' in modified_storage_parameters:
                            modified_storage_parameters['general-time']['name'] = modified_storage_parameters['general-time']['name'] + '|submitter-run-operation'

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