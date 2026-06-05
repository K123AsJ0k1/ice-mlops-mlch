# Works, but check
def path_workspace_check(
    properties: any,
    configs: any
) -> bool:
    print('Running workspace check')
    venv_path = configs['venv']['path']
    correct_path = False
    for workspace in properties['workspaces']:
        workspace_path = workspace['path']
        if venv_path == workspace_path:
            correct_path = True
            break
    print('Path is valid: ' + str(correct_path))
    return correct_path