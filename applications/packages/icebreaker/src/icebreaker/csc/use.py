def csc_source_command() -> str:
    return 'source /appl/profile/zz-csc-env.sh'

def csc_workspaces_command() -> str:
    return 'csc-workspaces'

def csc_create_venv_command(
    name: str
) -> str:
    command = 'python3 -m venv --system-site-packages ' + name
    return command