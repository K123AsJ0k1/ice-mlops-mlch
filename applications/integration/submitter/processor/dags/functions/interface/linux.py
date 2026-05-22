def linux_format_pwd(
    given_print: str
) -> str:
    formatted = given_print.split('\n')[0]
    directory = None
    if '/' in formatted:
        directory = formatted
    return directory

def linux_open_directory(
    path: str
) -> str:
    command = 'cd ' + path
    return command

def linux_list_directory() -> str:
    return 'ls'

def linux_format_list(
    resulted_print: str
) -> str:
    formatted_names = resulted_print.split('\n')[:-1]
    folders = []
    files = []
    for name in formatted_names:
        if '.' in name:
            files.append(name)
        else:
            folders.append(name)
    return folders, files

def linux_pwd_command() -> str:
    return 'pwd'

def linux_chmod_file(
    file_path: str
) -> str:
    command = 'chmod 600 ' + file_path
    return command