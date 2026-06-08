# check imports and function inputs
def collect_action_get_file(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    local_file_path: str,
    remote_file_path: str
) -> str:
    try:
        from pathlib import Path
        from functions.interface.sftp import sftp_retrieve_file
        from functions.interactions.bridge import bridge_ssh_interface
    except ImportError as e:
        raise ImportError("L3_orchestration_dags/tasks/fill_tasks failed to import", e)

    print('Run get file')
    local_path = None
    if 0 < len(local_file_path) and 0 < len(remote_file_path):
        retrieve_command = sftp_retrieve_file(
            local_file_path = local_file_path,
            remote_file_path = remote_file_path
        )
        print(retrieve_command)
        
        get_result = bridge_ssh_interface(
            storage_parameters = storage_parameters,
            lock_location = lock_location,
            interaction_parameters = {
                'platform': target_platform,
                'interface': 'sftp',
                'command': retrieve_command
            }
        )
        
        local_path = Path(local_file_path)
        if local_path.exists():
            if local_path.is_file():
                local_path = local_file_path
        
    print('Get file result: ' + str(local_path))
    return local_path 
# check imports and function inputs
def collect_action_get_sacct(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    commands: any,
    job_id: str
) -> any:
    try:
        from icebreaker.slurm.use import slurm_sacct_job
        from icebreaker.misc.general import fill_list_values
        from functions.interactions.bridge import bridge_ssh_interface
        from functions.utility.file import file_write_data
    except ImportError as e:
        raise ImportError("L3_orchestration_dags/tasks/fill_tasks failed to import", e)

    print('Run get sacct')

    sacct_command = slurm_sacct_job(
        job_id = job_id
    )

    get_command = fill_list_values(
        target = commands['slurm-sacct'],
        values = [
            sacct_command
        ]
    )   
    
    print(get_command)
    interaction_output = bridge_ssh_interface(
        storage_parameters = storage_parameters,
        lock_location = lock_location,
        interaction_parameters = {
            'platform': target_platform,
            'interface': 'ssh',
            'command': get_command
        }
    )
    
    print(interaction_output)
    sacct_name = target_platform + '-sacct-' + job_id + '.parquet' 
    sacct_path = file_write_data(
        name = sacct_name,
        data = interaction_output
    )
    
    print('Get sacct result:' + str(sacct_path))
    return sacct_path