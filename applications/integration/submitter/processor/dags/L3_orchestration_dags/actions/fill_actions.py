# Check imports and confirm function
def fill_action_utility_get_details(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    detail_key: str,
    commands: any
):  
    try: 
        from functions.interactions.bridge import bridge_ssh_interface
        from icebreaker.linux.utility import linux_format_pwd
        from icebreaker.csc.utility import csc_parse_workspaces
        from icebreaker.lmod.utility import lmod_parse_list
        from icebreaker.python.utility import python_parse_version
    except ImportError as e:
        raise ImportError("orchestration_dags/actions/fill_actions failed to import", e)

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