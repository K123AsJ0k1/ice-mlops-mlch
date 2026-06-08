 
def configure_task_cloud_interaction(
    swift_parameters: any,
    storage_parameters: any,
    platfrom_parameters: any
):
    try:
        import os
        from functions.utility.airflow import airflow_check_connection
        from functions.actions.sftp_actions import sftp_action_get_directory_list
        from functions.utility.file import file_write_data
    except ImportError as e:
        raise ImportError("L4_orchestration_dags/tasks/configure_tasks failed to import", e) 

    # This is single target, dags can make it multi target
    # This needs to use the provided controller env and input yaml
    # It then needs to use those details to replace files
    print('Configuration cloud interaction') 
    platform_name = platfrom_parameters['name']
    target_platform = 'cloud-' + platform_name
    print(f'Checking connections for {target_platform}')
    connection_exists = airflow_check_connection(
        connection_id = target_platform
    ) 
    print(f'Connection exists: {connection_exists}')
    checked_directories = {}
    if connection_exists:
        platform_configuration = platfrom_parameters['config']
        if 0 < len(platform_configuration):
            for configuration in platform_configuration:
                directory_path = configuration['directory_path']
                file_name = configuration['file_name']
                replace_file = configuration['replace']
                file_list = []
                if not directory_path in checked_directories:
                    file_list = sftp_action_get_directory_list(
                        storage_parameters = storage_parameters,
                        target_platform = target_platform,
                        target_path = directory_path
                    )
                    checked_directories[directory_path] = file_list
                else:
                    file_list = checked_directories[directory_path]
                
                if file_name in file_list:
                    if replace_file:
                        remote_file_path = os.path.join(directory_path, file_name) 
                        print(f'Replacing {remote_file_path}')
                        file_content = configuration['file_content']
                        local_file_path = file_write_data(
                            name = file_name,
                            data = file_content
                        )
                        print(local_file_path)
                       
    return None