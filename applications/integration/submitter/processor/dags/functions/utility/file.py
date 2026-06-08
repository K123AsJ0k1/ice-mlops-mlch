# check imports and function inputs
def file_storage_path(
    name: str
) -> str:
    try: 
        import os
    except ImportError as e:
        raise ImportError("functions/utility/files failed to import", e)
    # Might need chancing
    directory = 'submitter/files'
    os.makedirs(directory, exist_ok=True)
    file_path = directory + '/' + name
    return file_path
# check imports and function inputs
def file_write_data(
    name: str,
    data: any
) -> str:
    file_path = file_storage_path(
        name = name
    )
    with open(file_path, 'w', encoding = 'utf-8') as f:
        if isinstance(data, bytes):
            f.write(data.decode('utf-8'))
        if isinstance(data, str):
            f.write(data)
    return file_path
# check imports and function inputs
def file_chmod_command(
    file_path: str
) -> list:
    try: 
        from icebreaker.linux.use import linux_chmod_file
    except ImportError as e:
        raise ImportError("functions/utility/files failed to import", e)

    command_list = [
        linux_chmod_file(file_path = file_path)
    ]
    return command_list