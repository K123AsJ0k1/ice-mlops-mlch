#import copy
#import time as t

#from functions.dict import create_nested_dict, update_dict_value

#from functions.utility.misc import base_check_connection
#from functions.utility.platform import platform_fill_commands

#from functions.actions.fill import fill_get_details 
 
# works 
def fill_task_hpc_interaction( 
    swift_parameters: any,
    bucket_parameters: any,
    storage_parameters: any,
    platfrom_parameters: any
) -> any:  
    try:
        #from orchestration_dags.local_func.fill import fill_platform_interaction
        import copy
        import time as t
        from global_func.utility.airflow import airflow_check_connection
        from icebreaker.misc.dict import create_nested_dict, update_dict_value
    except ImportError as e:
        raise ImportError("orchestration_dags/local_func/fill failed to import", e)

    storage_dag_inputs = []
    platform_name = platfrom_parameters['name']
    target_platform = 'hpc-' + platform_name
    connection_exists = airflow_check_connection(
        connection_id = target_platform
    )
    print('Checking connections for ' + str(target_platform))
    if connection_exists:
        platform_fill_objects = platfrom_parameters['object-names']['fill']
        print('Checking amount of objects ' + str(len(platform_fill_objects)))
        if 0 < len(platform_fill_objects):
            fill_commands = platform_fill_commands(
                target_platform = target_platform
            ) 
            if 0 < len(fill_commands):
                platforms_path = 'platforms-' + platform_name
                properties_path = platforms_path + '-properties'
                state_path = platforms_path + '-state'
                
                root_dict = create_nested_dict(
                    target_dict = {},
                    key_path = properties_path,
                    separator = '-'
                ) 
                time_name = 'submitter-trigger|beat|celery|airflow|submitter-interaction-sequence|submitter-fill-operation'
                for object_name in platform_fill_objects:
                    platform_start_time = t.time()
                    print('Filling object ' + str(object_name))
                    properties_dict = {}
                    for key in fill_commands.keys():
                        given_value = fill_get_details(
                            storage_parameters = storage_parameters,
                            lock_location = storage_parameters['airflow-lock-location'], 
                            target_platform = target_platform,
                            detail_key = key,    
                            commands = fill_commands
                        )

                        if '-' in key:
                            properties_dict = create_nested_dict(
                                target_dict = properties_dict,
                                key_path = key,
                                separator = '-'
                            )
                            
                            update_dict_value(
                                target_dict = properties_dict,
                                key_path = key,
                                separator = '-',
                                new_value = given_value
                            )
                            
                            continue
                        properties_dict[key] = given_value

                    update_dict_value(
                        target_dict = root_dict,
                        key_path = properties_path,
                        separator = '-',
                        new_value = properties_dict
                    )
                    
                    update_dict = create_nested_dict(
                        target_dict = root_dict,
                        key_path = state_path,
                        separator = '-'
                    )
                    
                    update_dict_value(
                        target_dict = update_dict,
                        key_path = state_path,
                        separator = '-',
                        new_value = {
                            'interaction':{
                                'filled': True
                            },
                            'submitter':{
                                'operating': True
                            }
                        }
                    )
                    
                    modified_storage_parameters = copy.deepcopy(storage_parameters)
                    modified_storage_parameters['object-key'] = object_name.split('.')[0]
                    modified_storage_parameters['object-input'] = update_dict

                    if 'general-time' in modified_storage_parameters:
                        modified_storage_parameters['general-time']['name'] = modified_storage_parameters['general-time']['name'] + '|submitter-fill-operation'

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