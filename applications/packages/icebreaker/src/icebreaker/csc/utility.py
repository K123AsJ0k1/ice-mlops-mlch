
def csc_parse_workspaces(
    given_print: str
) -> any:
    row_format = given_print.split('\n')
    workspaces = []
    if 0 < len(row_format):
        valid_rows = [
            '/users/',
            '/project_'
        ]
        placement = [
            'path',
            'capacity',
            'files',
            'none'
        ]
        for row in row_format:
            if any(sub in row for sub in valid_rows):
                space = {
                    'path': None,
                    'capacity': None,
                    'files': None,
                }
                empty_split = row.split(' ')
                index = 0
                for case in empty_split:
                    if len(case) == 0:
                        continue
                    if index < 4:
                        place = placement[index]
                        if not place == 'none':
                            space[place] = case
                            if place == 'capacity' or place == 'files':
                                path_split = case.split('/')
                                used_key = 'used-' + place
                                max_key = 'max-' + place
                                space[used_key] = path_split[0]
                                space[max_key] = path_split[1]
                                del space[place]
                        index += 1
                workspaces.append(space)
    return workspaces

def csc_workspace_check(
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