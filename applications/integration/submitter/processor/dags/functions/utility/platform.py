from functions.utility.puhti import puhti_workspace_command, puhti_modules_command
from functions.utility.mahti import mahti_workspace_command, mahti_modules_command
from functions.utility.lumi import lumi_workspace_command, lumi_modules_command
from functions.interface.linux import linux_pwd_command, linux_list_directory
from functions.interface.python import python_version_command
from functions.interface.csc import csc_source_command
from functions.interface.venv import venv_upgrade_command, venv_list_command, venv_deactivate_command
from functions.dict import get_dict_value

def platform_fill_commands(
    target_platform: str
) -> any:
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

def platform_setup_commands(
    target_platform: str
) -> any:
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
                venv_upgrade_command(), 
                venv_deactivate_command()
            ],
            'venv-packages': [
                csc_source_command(), 
                None, 
                None, 
                venv_list_command(), 
                venv_deactivate_command()
            ],
            'venv-install': [
                csc_source_command(), 
                None, 
                None, 
                None, 
                venv_deactivate_command()
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
                venv_upgrade_command(), 
                venv_deactivate_command()
            ],
            'venv-packages': [
                csc_source_command(), 
                None, 
                None, 
                venv_list_command(), 
                venv_deactivate_command()
            ],
            'venv-install': [
                csc_source_command(), 
                None, 
                None, 
                None, 
                venv_deactivate_command()
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
                venv_upgrade_command(), 
                venv_deactivate_command()
            ],
            'venv-packages': [
                None,  
                None,
                venv_list_command(),
                venv_deactivate_command()
            ],
            'venv-install': [
                None, 
                None, 
                None, 
                venv_deactivate_command()
            ]
        }
    }

    if target_platform in platform_commands:
        for key, value in platform_commands[target_platform].items():
            setup_commands[key] = value
        return setup_commands
    return {}

def platform_setup_conditions(
    orchestration: any,
    properties_path: str,
    configs_path: str
) -> any:
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

def platform_run_commands(
    target_platform: str
) -> any:
    setup_commands = {
        'slurm-run': [],
        'slurm-check': []
    }
    # Sourcing is needed here
    platform_commands = {
        'hpc-puhti': {
            'slurm-run': [
                csc_source_command(),
                None
            ],
            'slurm-check': [
                csc_source_command(),
                None
            ]
        },
        'hpc-mahti': {
            'slurm-run': [
                csc_source_command(),
                None
            ],
            'slurm-check': [
                csc_source_command(),
                None
            ]
        },
        'hpc-lumi': {
            'slurm-run': [
                None
            ],
            'slurm-check': [
                None
            ]
        }
    }

    if target_platform in platform_commands:
        for key, value in platform_commands[target_platform].items():
            setup_commands[key] = value
        return setup_commands
    return {}

def platform_check_commands(
    target_platform: str
) -> any:
    setup_commands = {
        'slurm-check': [],
        'slurm-cancel': []
    }
    # Is sourcing needed here
    platform_commands = {
        'hpc-puhti': {
            'slurm-check': [
                csc_source_command(),
                None
            ],
            'slurm-cancel': [
                csc_source_command(),
                None,
                None
            ]
        },
        'hpc-mahti': {
            'slurm-check': [
                csc_source_command(),
                None
            ],
            'slurm-cancel': [
                csc_source_command(),
                None,
                None
            ]
        },
        'hpc-lumi': {
            'slurm-check': [
                None
            ],
            'slurm-cancel': [
                None,
                None
            ]
        }
    }

    if target_platform in platform_commands:
        for key, value in platform_commands[target_platform].items():
            setup_commands[key] = value
        return setup_commands
    return {}

def platform_collect_commands(
    target_platform: str 
) -> any:
    collect_commands = {
        'slurm-sacct': []
    }

    platform_commands = {
        'hpc-puhti': {
            'slurm-sacct': [
                csc_source_command(),
                None
            ]
        },
        'hpc-mahti': {
            'slurm-sacct': [
                csc_source_command(),
                None
            ]
        },
        'hpc-lumi': {
            'slurm-sacct': [
                None
            ]
        }
    }
    
    if target_platform in platform_commands:
        for key, value in platform_commands[target_platform].items():
            collect_commands[key] = value
        return collect_commands
    return {}
