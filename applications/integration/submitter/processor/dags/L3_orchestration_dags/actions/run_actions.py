# Check imports and confirm function
def run_action_submit_job(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    commands: any,
    file_path: str
) -> any:
    try: 
        from icebreaker.slurm.use import slurm_sbatch_job
        from icebreaker.slurm.utility import slurm_format_sbatch
        from icebreaker.misc.general import fill_list_values
        from functions.interactions.bridge import bridge_ssh_interface
    except ImportError as e:
        raise ImportError("L3_orchestration_dags/actions/run_actions failed to import", e)

    print('Run submit job')

    slurm_sbatch = slurm_sbatch_job(
        file_path = file_path
    )
    
    submit_command = fill_list_values(
        target = commands['slurm-run'],
        values = [
            slurm_sbatch
        ]
    )

    interaction_output = bridge_ssh_interface(
        storage_parameters = storage_parameters,
        lock_location = lock_location,
        interaction_parameters = {
            'platform': target_platform,
            'interface': 'ssh',
            'command': submit_command
        }
    )

    job_id = slurm_format_sbatch(
        resulted_print = interaction_output
    )
    
    print('Submit result: ' + str(job_id))
    return job_id
