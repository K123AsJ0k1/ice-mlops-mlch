def setup_utility_platform_commands(
    target_platform: str
) -> any:
    try: 
        from icebreaker.csc.use import csc_source_command
        from icebreaker.linux.use import linux_list_directory
        from icebreaker.python.use import (
            python_venv_upgrade_command,
            python_venv_deactivate_command,
            python_venv_list_command
        )
    except ImportError as e:
        raise ImportError("L3_orchestration_dags/utility/setup_utility failed to import", e)

    setup_commands = {
        'venv-check': [],
        'venv-create': [],
        'venv-packages': [],
        'venv-install': []
    }
    # Does venv check require sourcing for puhti and mahti
    platform_commands = {
        'hpc-puhti': {
            'venv-check': [
                csc_source_command(), 
                None, 
                linux_list_directory()
            ],
            'venv-create': [
                csc_source_command(), 
                None, 
                None, 
                None, 
                None, 
                python_venv_upgrade_command(), 
                python_venv_deactivate_command()
            ],
            'venv-packages': [
                csc_source_command(), 
                None, 
                None, 
                python_venv_list_command(), 
                python_venv_deactivate_command()
            ],
            'venv-install': [
                csc_source_command(), 
                None, 
                None, 
                None, 
                python_venv_deactivate_command()
            ]
        },
        'hpc-mahti': {
            'venv-check': [
                csc_source_command(), 
                None, 
                linux_list_directory()
            ],
            'venv-create': [
                csc_source_command(), 
                None, 
                None, 
                None, 
                None, 
                python_venv_upgrade_command(), 
                python_venv_deactivate_command()
            ],
            'venv-packages': [
                csc_source_command(), 
                None, 
                None, 
                python_venv_list_command(), 
                python_venv_deactivate_command()
            ],
            'venv-install': [
                csc_source_command(), 
                None, 
                None, 
                None, 
                python_venv_deactivate_command()
            ]
        },
        'hpc-lumi': {
            'venv-check': [
                None, 
                linux_list_directory()
            ],
            'venv-create': [
                None, 
                None, 
                None, 
                None, 
                python_venv_upgrade_command(), 
                python_venv_deactivate_command()
            ],
            'venv-packages': [
                None,  
                None,
                python_venv_list_command(), 
                python_venv_deactivate_command()
            ],
            'venv-install': [
                None, 
                None, 
                None, 
                python_venv_deactivate_command()
            ]
        }
    }

    if target_platform in platform_commands:
        for key, value in platform_commands[target_platform].items():
            setup_commands[key] = value
        return setup_commands
    return {}

def setup_utility_platform_conditions(
    orchestration: any,
    properties_path: str,
    configs_path: str
) -> any:
    try: 
        from icebreaker.misc.dict import get_dict_value
    except ImportError as e:
        raise ImportError("L3_orchestration_dags/utility/setup_utility failed to import", e)

    # This might need reconsideration later
    platform_properties = get_dict_value(
        target_dict = orchestration,
        key_path = properties_path,
        separator = '-'
    )

    platform_configs = get_dict_value(
        target_dict = orchestration,
        key_path = configs_path,
        separator = '-'
    )
    
    platform_conditions = [
        {
            'purpose': 'Is venv path in the workspace',
            'wanted': 'value-bool-true',
            'check': 'workspace-check',
            'params': [
                platform_properties,
                platform_configs
            ]
        },
        {
            'purpose': 'Does venv exist',
            'wanted': 'list-bool-true',
            'check': 'venv-check',
            'params': [
                platform_configs
            ]
        },
        {
            'purpose': 'Create missing venv',
            'wanted': 'value-bool-true',
            'check': 'venv-create',
            'params': [
                platform_configs
            ]
        },
        {
            'purpose': 'Are the wanted packages in the venv',
            'wanted': 'list-bool-true',
            'check': 'venv-packages',
            'params': [
                platform_configs
            ]
        },
        {
            'purpose': 'Install missing packages',
            'wanted': 'value-bool-true',
            'check': 'venv-install',
            'params': [
                platform_configs
            ]
        }
    ]
    return platform_conditions