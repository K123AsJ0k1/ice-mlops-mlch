from functions.interface.sftp import sftp_list_directory
from functions.interactions.platform import platform_interface_interaction
 
# Works
def general_list_directory(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    target_path: str
) -> any:
    print('Run list directory')

    directory_command = sftp_list_directory(
        target_path = target_path
    )

    file_list = platform_interface_interaction(
        storage_parameters = storage_parameters,
        lock_location = lock_location,
        interaction_parameters = {
            'platform': target_platform,
            'interface': 'sftp',
            'command': directory_command
        }
    )
    print('Listed files: ', file_list)
    return file_list