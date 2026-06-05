
def mahti_workspace_command() -> list:
    try:
        from ..csc.use import csc_source_command, csc_workspaces_command
    except ImportError as e:
        raise ImportError("mahti/use failed to import", e)

    command_list = [
        csc_source_command(),
        csc_workspaces_command()
    ]
    return command_list

def mahti_modules_command() -> list:
    try:
        from ..csc.use import csc_source_command
        from ..lmod.use import lmod_list_command
    except ImportError as e:
        raise ImportError("mahti/use failed to import", e)

    command_list = [
        csc_source_command(),
        lmod_list_command()
    ]
    return command_list