from functions.interface.slurm import slurm_squeue_jobs
 
def jobs_check_execution() -> any:
    command_list = [
        slurm_squeue_jobs()
    ]
    return command_list