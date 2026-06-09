# Works
def configure_task_cloud_interaction(
    storage_parameters: any,
    platfrom_parameters: any
):
    try:
        from functions.utility.airflow import airflow_check_connection
        from functions.actions.sftp_actions import (
            sftp_action_get_directory_list, 
            sftp_action_send_file
        )
    except ImportError as e:
        raise ImportError("L4_orchestration_dags/tasks/configure_tasks failed to import", e) 
    # This is single target, dags can make it multi target
    print('Configuration cloud interaction') 
    platform_name = platfrom_parameters['name']
    target_platform = 'cloud-' + platform_name
    print(f'Checking connections for {target_platform}')
    connection_exists = airflow_check_connection(
        connection_id = target_platform
    ) 
    print(f'Connection exists: {connection_exists}')
    checked_directories = {}
    cloud_configured = False
    if connection_exists:
        platform_configuration = platfrom_parameters['config']
        if 0 < len(platform_configuration):
            for configuration in platform_configuration:
                directory_path = configuration['directory_path']
                file_name = configuration['file_name']
                file_content = configuration['file_content']
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
                
                send_file = True
                if file_name in file_list:
                    if not replace_file:
                        send_file = False

                if send_file:
                    cloud_configured = sftp_action_send_file(
                        storage_parameters = storage_parameters,
                        target_platform = target_platform,
                        directory_path = directory_path,
                        file_name = file_name,
                        file_content = file_content
                    )
    return cloud_configured