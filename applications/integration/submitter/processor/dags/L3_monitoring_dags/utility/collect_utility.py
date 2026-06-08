# check imports and function inputs
def collect_utility_platform_commands(
    target_platform: str 
) -> any:
    try:
        from icebreaker.csc.use import csc_source_command
    except ImportError as e:
        raise ImportError("L3_monitoring_dags/utility/collect_utility failed to import", e)

    collect_commands = {
        'slurm-sacct': []
    }

    platform_commands = {
        'hpc-puhti': {
            'slurm-sacct': [
                csc_source_command(),
                None
            ]
        },
        'hpc-mahti': {
            'slurm-sacct': [
                csc_source_command(),
                None
            ]
        },
        'hpc-lumi': {
            'slurm-sacct': [
                None
            ]
        }
    }
    
    if target_platform in platform_commands:
        for key, value in platform_commands[target_platform].items():
            collect_commands[key] = value
        return collect_commands
    return {}

def collect_utility_job_validity(
    valid_jobs: list,
    job_index: int
) -> bool:
    valid = False
    for filter in valid_jobs:
        if filter == 'all':
            valid = True
            break
        if filter == str(job_index):
            valid = True
    return valid