import os

from functions.interface.linux import linux_chmod_file

def files_storage_path(
    name: str
) -> str:
    # Might need chancing
    directory = 'submitter/files'
    os.makedirs(directory, exist_ok=True)
    file_path = directory + '/' + name
    return file_path

def files_write_data(
    name: str,
    data: any
) -> str:
    file_path = files_storage_path(
        name = name
    )
    with open(file_path, 'w', encoding = 'utf-8') as f:
        if isinstance(data, bytes):
            f.write(data.decode('utf-8'))
        if isinstance(data, str):
            f.write(data)
    return file_path

def files_chmod_command(
    file_path: str
) -> list:
    command_list = [
        linux_chmod_file(file_path = file_path)
    ]
    return command_list