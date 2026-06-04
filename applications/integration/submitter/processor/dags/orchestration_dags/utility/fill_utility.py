#from functions.interface.linux import linux_format_pwd
#from functions.interface.csc import csc_parse_workspaces
#from functions.interface.lmod import lmod_parse_list
#from functions.interface.python import python_parse_version 

#from functions.interactions.platform import platform_interface_interaction
# works 
def details_get_fill(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    detail_key: str,
    commands: any
):  
    try: 
        from orchestration_dags.tasks.fill_tasks import fill_task_hpc_interaction
    except ImportError as e:
        raise ImportError("orchestration_dags/fill failed to import", e)

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

#from functions.utility.puhti import puhti_workspace_command, puhti_modules_command
#from functions.utility.mahti import mahti_workspace_command, mahti_modules_command
#from functions.utility.lumi import lumi_workspace_command, lumi_modules_command
#from functions.interface.linux import linux_pwd_command, linux_list_directory
#from functions.interface.python import python_version_command
#from functions.interface.csc import csc_source_command
#from functions.interface.venv import venv_upgrade_command, venv_list_command, venv_deactivate_command
#from functions.dict import get_dict_value

def platform_fill_commands(
    target_platform: str
) -> any:
    try: 
        from orchestration_dags.tasks.fill_tasks import fill_task_hpc_interaction
    except ImportError as e:
        raise ImportError("orchestration_dags/fill failed to import", e)

    # In the future this might need to 
    # consider other things besides properties
    fill_commands = {
        'directory': [
            linux_pwd_command()
        ],
        'workspaces': [],
        'languages-python': [
            python_version_command()
        ],
        'modules': []
    }

    platform_commands = {
        'hpc-puhti': {
            'workspaces': puhti_workspace_command(),
            'modules': puhti_modules_command()
        },
        'hpc-mahti': {
            'workspaces': mahti_workspace_command(),
            'modules': mahti_modules_command()
        },
        'hpc-lumi': {
            'workspaces': lumi_workspace_command(),
            'modules': lumi_modules_command()
        }
    }

    if target_platform in platform_commands:
        for key, value in platform_commands[target_platform].items():
            fill_commands[key] = value
        return fill_commands
    return {}