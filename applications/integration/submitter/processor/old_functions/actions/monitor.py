from functions.general import fill_list_values

from functions.interface.slurm import slurm_squeue_jobs, slurm_scancel_job, slurm_format_squeue
from functions.interactions.platform import platform_interface_interaction

# Works
def monitor_check_jobs(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    commands: any
) -> any:
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
# Works
def monitor_cancel_job(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    commands: any,
    job_id: str
) -> any:
    print('Run cancel job')

    scancel_command = slurm_scancel_job(
        job_id = job_id
    )
    
    squeue_command = slurm_squeue_jobs()
    
    cancel_command = fill_list_values(
        target = commands['slurm-cancel'],
        values = [
            scancel_command,
            squeue_command
        ]
    )

    interaction_output = platform_interface_interaction(
        storage_parameters = storage_parameters,
        lock_location = lock_location,
        interaction_parameters = {
            'platform': target_platform,
            'interface': 'ssh',
            'command': cancel_command
        }
    )

    current_jobs = slurm_format_squeue(
        resulted_print = interaction_output
    )
    
    print('Cancel result:', current_jobs)
    return current_jobs