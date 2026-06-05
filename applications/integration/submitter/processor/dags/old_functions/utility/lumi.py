from functions.interface.lumi import lumi_workspaces_command
from functions.interface.lmod import lmod_list_command
 
def lumi_workspace_command() -> list:
    command_list = [
        lumi_workspaces_command()
    ]
    return command_list

def lumi_modules_command() -> list:
    command_list = [
        lmod_list_command()
    ]
    return command_list