def python_version_command() -> str:
    return 'python3 -V'

def python_venv_upgrade_command() -> str:
    return 'pip install --upgrade pip'

def python_venv_activate_command(
    path: str,
    name: str
) -> str:
    command = ''
    if 0 < len(path):
        command = 'source ' + path + '/' + name + '/bin/activate'
    else:
        command = 'source ' + name + '/bin/activate'
    return command

def python_venv_list_command() -> str:
    return 'pip list --disable-pip-version-check'

def python_venv_deactivate_command() -> str:
    return 'deactivate'

def python_venv_install_command(
    wanted_packages: any
) -> any:
    command = 'pip install'
    for package in wanted_packages:
        command += ' ' + package 
    return command