def platform_collect_commands(
    target_platform: str 
) -> any:
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