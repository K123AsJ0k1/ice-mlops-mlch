# check imports and function inputs
def check_utility_platform_commands(
    target_platform: str
) -> any:
    try: 
        from icebreaker.csc.use import csc_source_command
    except ImportError as e:
        raise ImportError("orchestration_dags/utility/fill_utility failed to import", e)

    setup_commands = {
        'slurm-check': [],
        'slurm-cancel': []
    } 
    # Is sourcing needed here
    # The scancel and squeue commands could be added here
    platform_commands = {
        'hpc-puhti': {
            'slurm-check': [
                csc_source_command(),
                None
            ],
            'slurm-cancel': [
                csc_source_command(),
                None,
                None
            ]
        },
        'hpc-mahti': {
            'slurm-check': [
                csc_source_command(),
                None
            ],
            'slurm-cancel': [
                csc_source_command(),
                None,
                None
            ]
        },
        'hpc-lumi': {
            'slurm-check': [
                None
            ],
            'slurm-cancel': [
                None,
                None
            ]
        }
    }

    if target_platform in platform_commands:
        for key, value in platform_commands[target_platform].items():
            setup_commands[key] = value
        return setup_commands
    return {}