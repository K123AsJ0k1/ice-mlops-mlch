#from functions.general import fill_list_values

#from functions.interface.slurm import slurm_sbatch_job, slurm_format_sbatch
#from functions.interactions.platform import platform_interface_interaction
  
# Works
def run_action_submit_job(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    commands: any,
    file_path: str
) -> any:
    try: 
        #from functions.interactions.bridge import bridge_ssh_interface
        #from icebreaker.linux.utility import linux_format_pwd
        #from icebreaker.csc.utility import csc_parse_workspaces
        #from icebreaker.lmod.utility import lmod_parse_list
        #from icebreaker.python.utility import python_parse_version
        from icebreaker.slurm.use import slurm_sbatch_job
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

    interaction_output = platform_interface_interaction(
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
