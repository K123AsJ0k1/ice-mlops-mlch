# Check imports and confirm function
def setup_task_hpc_configs(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    orchestration: any
) -> any:
    try:
        
        from icebreaker.csc.utility import csc_workspace_check
        from L3_orchestration_dags.utility.setup_utility import (
            setup_utility_platform_commands,
            setup_utility_platform_conditions
        )
        from L3_orchestration_dags.actions.setup_actions import (
            setup_action_venv_create,
            setup_action_venv_install,
            setup_action_venv_check,
            setup_action_venv_packages
        )
    except ImportError as e:
        raise ImportError("L3_orchestration_dags/tasks/fill_tasks failed to import", e) 

    status = False
    setup_commands = setup_utility_platform_commands(
        target_platform = target_platform
    ) 
    if 0 < len(setup_commands):
        platform_name = target_platform.split('-')[-1]
        platforms_path = 'platforms-' + platform_name
        properties_path = platforms_path + '-properties'
        configs_path = platforms_path + '-configs'
        
        platform_conditions = setup_utility_platform_conditions(
            orchestration = orchestration,
            properties_path = properties_path,
            configs_path = configs_path
        ) 

        index = 0
        condition_results = []
        for condition in platform_conditions:
            wanted = condition['wanted']
            check = condition['check']
            check_result = False
            if 'value-bool-true' == wanted:
                if check == 'workspace-check':
                    check_result = csc_workspace_check(
                        properties = platform_conditions[index]['params'][0],
                        configs = platform_conditions[index]['params'][1]
                    )
                if check == 'venv-create':
                    if not condition_results[1]:
                        check_result = setup_action_venv_create(
                            storage_parameters = storage_parameters,
                            lock_location = lock_location,
                            target_platform = target_platform,
                            commands = setup_commands,
                            configs = platform_conditions[index]['params'][0]
                        )
                if check == 'venv-install':
                    if 0 < len(condition_results[3]):
                        check_result = setup_action_venv_install(
                            storage_parameters = storage_parameters,
                            lock_location = lock_location,
                            target_platform = target_platform,
                            commands = setup_commands,
                            configs = platform_conditions[index]['params'][0]
                        )
            if 'list-bool-true' == wanted:
                if check == 'venv-check': 
                    if condition_results[0]:
                        check_result = setup_action_venv_check(
                            storage_parameters = storage_parameters,
                            lock_location = lock_location,
                            target_platform = target_platform,
                            commands = setup_commands,
                            configs = platform_conditions[index]['params'][0]
                        )
                if check == 'venv-packages':
                    if condition_results[1] or condition_results[2]:
                        check_result = setup_action_venv_packages(
                            storage_parameters = storage_parameters,
                            lock_location = lock_location,
                            target_platform = target_platform,
                            commands = setup_commands,
                            configs = platform_conditions[index]['params'][0]
                        )
            condition_results.append(check_result)
            index += 1
        
        if condition_results[0]:
            if condition_results[1] or condition_results[2]:
                if 0 == len(condition_results[3]) or condition_results[4]:
                    print('Config conditions: ', condition_results)
                    status = True
    return status
# Check imports and confirm function
def setup_task_hpc_files(
    swift_client: any,
    bucket_parameters: any,
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    orchestration: any
) -> any:
    try:
        from icebreaker.misc.dict import get_dict_value
        from functions.actions.sftp_actions import sftp_action_get_directory_list
        from L3_orchestration_dags.actions.setup_actions import setup_action_send_file
    except ImportError as e:
        raise ImportError("L3_orchestration_dags/tasks/fill_tasks failed to import", e) 

    status = True

    platform_name = target_platform.split('-')[-1]
    platforms_path = 'platforms-' + platform_name
    properties_workspaces_path = platforms_path + '-properties-workspaces'
    files_send_path = platforms_path + '-files-send'
    
    platform_properties_workspace = get_dict_value(
        target_dict = orchestration,
        key_path = properties_workspaces_path,
        separator = '-'
    )

    platform_send_files = get_dict_value(
        target_dict = orchestration,
        key_path = files_send_path,
        separator = '-'
    )
     
    operation_results = []
    for operation in platform_send_files:
        transfer = operation['transfer']
        overwrite = None
        if 'overwrite' in operation:
            overwrite = operation['overwrite']
        transfer_source = transfer['source']
        transfer_target = transfer['target']
        operation_result = False
        if transfer_target['place'] == 'hpc':
            target_file_path = transfer_target['path']
            for workspace in platform_properties_workspace:
                workspace_path = workspace['path']
                if workspace_path in target_file_path:
                    file_list = sftp_action_get_directory_list(
                        storage_parameters = storage_parameters,
                        lock_location = lock_location,
                        target_platform = target_platform,
                        target_path = workspace_path
                    )
                    # Check if this needs to be changed into handle lists
                    run_operation = True
                    file_name = target_file_path.split('/')[-1]
                    # This can take none
                    if file_name in file_list:
                        if not overwrite:
                            run_operation = False
                            operation_result = True
                            operation_results.append(operation_result)
                    
                    if run_operation:
                        operation_result = setup_action_send_file(
                            swift_client = swift_client,
                            bucket_parameters = bucket_parameters,
                            storage_parameters = storage_parameters,
                            lock_location = lock_location,
                            target_platform = target_platform,
                            transfer_source = transfer_source,
                            transfer_target = transfer_target
                        )
                        operation_results.append(operation_result)             
    
    for result in operation_results:
        if not result:
            print('Setup results: ', operation_results)
            status = False
            break
    return status
# Check imports and confirm function
def setup_task_hpc_interaction(
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
        from icebreaker.swift.setup import swift_setup_client
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
        platform_setup_objects = platfrom_parameters['object-names']['setup']
        print('Checking amount of objects ' + str(len(platform_setup_objects)))
        if 0 < len(platform_setup_objects):
            swift_client = swift_setup_client(
                swift_parameters = swift_parameters
            )
            bucket_target = bucket_parameters['target']
            bucket_prefix = bucket_parameters['prefix']
            bucket_user = bucket_parameters['user']
            debug_prints = storage_parameters['debug-prints']

            time_name = 'submitter-trigger|beat|celery|airflow|submitter-interaction-sequence|submitter-setup-operation'
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
                
                config_status = setup_task_hpc_configs(
                    storage_parameters = storage_parameters,
                    lock_location = storage_parameters['airflow-lock-location'],
                    target_platform = target_platform,
                    orchestration = orch_data
                )
                print('Config setup success: ' + str(config_status))
                
                files_status = setup_task_hpc_files(
                    swift_client = swift_client,
                    bucket_parameters = bucket_parameters,
                    storage_parameters = storage_parameters,
                    lock_location = storage_parameters['airflow-lock-location'],
                    target_platform = target_platform,
                    orchestration = orch_data
                )
                print('File setup success: ' + str(files_status))
                if config_status and files_status:
                    platforms_path = 'platforms-' + platform_name
                    interaction_path = platforms_path + '-state-interaction'
                    
                    update_dict = create_nested_dict(
                        target_dict = {},
                        key_path = interaction_path,
                        separator = '-'
                    )
                    
                    update_dict_value(
                        target_dict = update_dict,
                        key_path = interaction_path,
                        separator = '-',
                        new_value = {'setup': True}
                    )

                    modified_storage_parameters = copy.deepcopy(storage_parameters)
                    modified_storage_parameters['object-key'] = object_name.split('.')[0]
                    modified_storage_parameters['object-input'] = update_dict
                    
                    if 'general-time' in modified_storage_parameters:
                        modified_storage_parameters['general-time']['name'] = modified_storage_parameters['general-time']['name'] + '|submitter-setup-operation'

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
    