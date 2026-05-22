from functions.interface.linux import linux_format_pwd
from functions.interface.csc import csc_parse_workspaces
from functions.interface.lmod import lmod_parse_list
from functions.interface.python import python_parse_version 

from functions.interactions.platform import platform_interface_interaction
# works 
def fill_get_details(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    detail_key: str,
    commands: any
): 
    print('Running get details')
    
    filled_details = None
    fill_command = commands[detail_key]
    interaction_output = platform_interface_interaction(
        storage_parameters = storage_parameters,
        lock_location = lock_location,
        interaction_parameters = {
            'platform': target_platform,
            'interface': 'ssh',
            'command': fill_command
        }
    )
    
    filled_details = 'filled'
    if not interaction_output is None:
        if 'directory' in detail_key:
            filled_details = linux_format_pwd(
                given_print = interaction_output
            )
        if 'workspaces' in detail_key:
            filled_details = csc_parse_workspaces(
                given_print = interaction_output
            )
        if 'modules' in detail_key:
            filled_details = lmod_parse_list(
                given_print = interaction_output
            )
        if 'python' in detail_key:
            filled_details = python_parse_version(
                given_print = interaction_output
            )
    
    return filled_details