# check imports and function inputs
def monitor_action_check_jobs(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    commands: any
) -> any:
    try:
        from icebreaker.slurm.use import slurm_squeue_jobs
        from icebreaker.misc.general import fill_list_values
        from functions.interactions.bridge import bridge_ssh_interface
        from icebreaker.slurm.utility import slurm_format_squeue
    except ImportError as e:
        raise ImportError("L3_orchestration_dags/tasks/fill_tasks failed to import", e) 

    print('Run check jobs')

    squeue_command = slurm_squeue_jobs()

    check_command = fill_list_values(
        target = commands['slurm-check'],
        values = [
            squeue_command
        ]
    )
    
    interaction_output = bridge_ssh_interface(
        storage_parameters = storage_parameters,
        lock_location = lock_location,
        interaction_parameters = {
            'platform': target_platform,
            'interface': 'ssh',
            'command': check_command
        }
    )

    current_jobs = slurm_format_squeue(
        resulted_print = interaction_output
    )
    
    print('Check result:', current_jobs)
    return current_jobs