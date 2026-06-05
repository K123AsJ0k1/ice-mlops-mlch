from functions.interface.csc import csc_source_command, csc_workspaces_command
from functions.interface.lmod import lmod_list_command
 
def mahti_workspace_command() -> list:
    command_list = [
        csc_source_command(),
        csc_workspaces_command()
    ]
    return command_list

def mahti_modules_command() -> list:
    command_list = [
        csc_source_command(),
        lmod_list_command()
    ]
    return command_list