def linux_open_directory(
    path: str
) -> str:
    command = 'cd ' + path
    return command

def linux_list_directory() -> str:
    return 'ls'

def linux_pwd_command() -> str:
    return 'pwd'

def linux_chmod_file(
    file_path: str
) -> str:
    command = 'chmod 600 ' + file_path
    return command