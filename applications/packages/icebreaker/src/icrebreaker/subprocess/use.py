def subprocess_run_command(
    command: any
) -> any: 
    try:
        import subprocess
    except ImportError as e:
        raise ImportError("Failed to import", e)

    resulted_print = subprocess.run(
        command,
        shell = True,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )

    print_output = resulted_print.stdout.decode('utf-8').split('\n')
    print_errors = resulted_print.stderr.decode('utf-8').split('\n')
    return print_output, print_errors