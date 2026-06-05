def lumi_workspaces_command() -> str:
    return 'lumi-workspaces'

def lumi_workspace_command() -> list:
    command_list = [
        lumi_workspaces_command()
    ]
    return command_list

def lumi_modules_command() -> list:
    try:
        from ..lmod.use import lmod_list_command
    except ImportError as e:
        raise ImportError("mahti/use failed to import", e)
    
    command_list = [
        lmod_list_command()
    ]
    return command_list