
# check imports and function inputs
def fill_utility_platform_commands(
    target_platform: str
) -> any:
    try: 
        from icebreaker.linux.use import linux_pwd_command
        from icebreaker.python.use import python_version_command
        from icebreaker.puhti.use import puhti_workspace_command, puhti_modules_command
        from icebreaker.mahti.use import mahti_workspace_command, mahti_modules_command
        from icebreaker.lumi.use import lumi_workspace_command, lumi_modules_command
    except ImportError as e:
        raise ImportError("orchestration_dags/utility/fill_utility failed to import", e)

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
# Check imports and confirm function
def fill_utility_get_details(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    detail_key: str,
    commands: any
):  
    try: 
        from global_functions.interactions.bridge import bridge_ssh_interface
        from icebreaker.linux.utility import linux_format_pwd
        from icebreaker.csc.utility import csc_parse_workspaces
        from icebreaker.lmod.utility import lmod_parse_list
        from icebreaker.python.utility import python_parse_version
    except ImportError as e:
        raise ImportError("orchestration_dags/utility/fill_utility failed to import", e)

    print('Running get details')
    
    filled_details = None
    fill_command = commands[detail_key]
    interaction_output = bridge_ssh_interface(
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