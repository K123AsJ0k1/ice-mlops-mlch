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