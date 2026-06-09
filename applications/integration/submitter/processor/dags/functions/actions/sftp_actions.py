# Works
def sftp_action_get_directory_list(
    storage_parameters: any,
    target_platform: str,
    target_path: str
) -> any:
    try:
        from functions.utility.sftp import sftp_list_directory
        from functions.interactions.bridge import bridge_interface_interaction
    except ImportError as e:
        raise ImportError("functions/actions/sftp failed to import", e) 

    print('Run sftp action get directory list')

    directory_command = sftp_list_directory(
        target_path = target_path
    )

    file_list = []
    try:
        file_list = bridge_interface_interaction(
            storage_parameters = storage_parameters,
            interaction_parameters = {
                'platform': target_platform,
                'interface': 'sftp',
                'command': directory_command
            }
        )
    except Exception as e:
        print('sftp_action_get_directory_list failed')

    print('Listed files: ', file_list)
    return file_list

def sftp_action_send_file(
    storage_parameters: any,
    target_platform: str,
    directory_path: str,
    file_name: str,
    file_content: any
):
    try:
        import os
        from functions.utility.file import file_write_data
        from functions.utility.sftp import stfp_store_file
        from functions.interactions.bridge import bridge_interface_interaction
    except ImportError as e:
        raise ImportError("functions/actions/sftp_actions failed to import", e)
    
    print('Run sftp action send file')
    remote_file_path = os.path.join(directory_path, file_name) 
    print(f'Creating file {remote_file_path}')
    local_file_path = file_write_data(
        name = file_name,
        data = file_content
    )
    
    store_command = stfp_store_file(
        local_file_path = local_file_path,
        remote_file_path = remote_file_path
    )
    
    send_result = bridge_interface_interaction(
        storage_parameters = storage_parameters,
        interaction_parameters = {
            'platform': target_platform,
            'interface': 'sftp',
            'command': store_command
        }
    )
    file_sent = False
    if not send_result is None:
        print(f'File creation/editing succesful')
        file_sent = True
    else:
        print(f'File creation/editing failed')
    return file_sent
    
