
def slurm_sbatch_job(
    file_path: str
) -> str:
    command = 'sbatch ' + file_path
    return command

def slurm_squeue_jobs() -> str:
    try:
        from ..slurm.utility import slurm_squeue_columns
    except ImportError as e:
        raise ImportError("slurm/use failed to import", e)

    columns_command = slurm_squeue_columns()
    command = 'squeue --me' + columns_command
    return command

def slurm_scancel_job(
    job_id: str
) -> str:
    command = 'scancel ' + job_id
    return command

def slurm_seff_job(
    job_id: str
) -> str:
    command = 'seff ' + job_id
    return command

def slurm_sacct_job(
    job_id: str
) -> str:
    try:
        from ..slurm.utility import slurm_sacct_metrics
    except ImportError as e:
        raise ImportError("slurm/use failed to import", e)

    formatting_command = slurm_sacct_metrics()
    command = 'sacct -j ' + job_id + formatting_command
    return command
