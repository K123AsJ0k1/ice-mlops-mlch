# check imports and function inputs
def run_utility_platform_commands(
    target_platform: str
) -> any:
    try: 
        from icebreaker.csc.use import csc_source_command
    except ImportError as e:
        raise ImportError("orchestration_dags/utility/run_utility failed to import", e)

    setup_commands = {
        'slurm-run': [],
        'slurm-check': []
    }
    # Sourcing is needed here
    platform_commands = {
        'hpc-puhti': {
            'slurm-run': [
                csc_source_command(),
                None
            ],
            'slurm-check': [
                csc_source_command(),
                None
            ]
        },
        'hpc-mahti': {
            'slurm-run': [
                csc_source_command(),
                None
            ],
            'slurm-check': [
                csc_source_command(),
                None
            ]
        },
        'hpc-lumi': {
            'slurm-run': [
                None
            ],
            'slurm-check': [
                None
            ]
        }
    }

    if target_platform in platform_commands:
        for key, value in platform_commands[target_platform].items():
            setup_commands[key] = value
        return setup_commands
    return {}