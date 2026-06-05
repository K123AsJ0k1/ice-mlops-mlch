def sftp_list_directory(
    target_path: str        
) -> any:
    command = ['list-directory', target_path]
    return command

def stfp_store_file(
    local_file_path: str,
    remote_file_path: str
) -> any:
    command = ['store-file', remote_file_path, local_file_path]
    return command

def sftp_retrieve_file(
    local_file_path: str,
    remote_file_path: str
) -> any:
    command = ['retrieve-file', remote_file_path, local_file_path]
    return command