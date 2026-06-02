
def docker_start_compose(
    file_path: str
) -> bool:
    try:
        import subprocess
        import os
    except ImportError as e:
        raise ImportError("docker/use failed to import", e)
    
    if not os.path.exists(file_path):
        print(f"File not found at {file_path}")
        return False
    
    compose_up_command = f'docker compose -f "{file_path}" up -d'

    result = subprocess.run(
        compose_up_command,
        capture_output = True,
        text = True,
        shell = True
    )

    if result.returncode == 0:
        print("Environment started successfully.")
        return True
    else:
        print(f"Failed to start environment: {result.stderr}")
        return False

def docker_stop_compose(
    file_path: str
) -> bool:
    try:
        import subprocess
        import os
    except ImportError as e:
        raise ImportError("docker/use failed to import", e)
    
    if not os.path.exists(file_path):
        print(f"File not found at {file_path}")
        return False
    
    compose_down_command = f'docker compose -f "{file_path}" down'

    result = subprocess.run(
        compose_down_command,
        capture_output = True,
        text = True,
        shell = True
    )

    if result.returncode == 0:
        print("Environment stopped and cleaned up successfully.")
        return True
    else:
        print(f"Failed to stop environment: {result.stderr}")
        return False
    
def docker_check_compose(
    file_path: str
) -> bool:
    try:
        import subprocess
        import os
    except ImportError as e:
        raise ImportError("docker/use failed to import", e)
    
    if not os.path.exists(file_path):
        print(f"File not found at {file_path}")
        return False
    
    compose_check_command = f'docker compose -f "{file_path}" ps --format json'

    try:
        result = subprocess.run(
            compose_check_command,
            capture_output=True,
            text=True,
            check=True,
            shell=True
        )

        output = result.stdout.strip()
        
        return len(output) > 2 
    except Exception as e:
        return False
    
def docker_manage_compose(
    file_path: str,
    current_state: str,
    wanted_state: bool
):
    print(f"Managing compose file: {file_path}")
    print(f"Current state: {current_state}")
    if current_state == 'UNKNOWN':
        print('Checking current compose state')
        check_docker_compose = docker_check_compose(
            file_path = file_path
        )
        if check_docker_compose:
            current_state = 'RUNNING'
        else:
            current_state = 'STOPPED'
    print(f"Wanted state: {wanted_state}")
    if not current_state == 'RUNNING' and wanted_state:
        print('Starting docker compose file')
        start_state = docker_start_compose(
            file_path = file_path
        ) 
        if start_state:
            current_state = 'RUNNING'
    if not current_state == 'STOPPED' and not wanted_state:
        print('Stopping docker compose file')
        stop_state = docker_stop_compose(
            file_path = file_path
        )
        if stop_state:
            current_state == 'STOPPED'
    return current_state

        