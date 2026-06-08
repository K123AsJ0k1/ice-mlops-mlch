# check imports and function inputs
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