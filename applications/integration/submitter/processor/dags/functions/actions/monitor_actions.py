#from functions.general import fill_list_values

#from functions.interface.slurm import slurm_squeue_jobs, slurm_scancel_job, slurm_format_squeue
#from functions.interactions.platform import platform_interface_interaction

# Works
def monitor_check_jobs(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    commands: any
) -> any:
    try:
        from icebreaker.slurm.use import slurm_squeue_jobs
        #from icebreaker
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
    
    interaction_output = platform_interface_interaction(
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