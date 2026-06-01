
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

    compose_up_command = [
        "docker", 
        "compose", 
        "-f", 
        file_path, 
        "up", 
        "-d"
    ]

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
        print(f"Failed to start environment.\nError:\n{result.stderr}")
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

    compose_down_command = [
        "docker", 
        "compose", 
        "-f", 
        file_path, 
        "down"
    ]

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
        print(f"Failed to stop environment.\nError:\n{result.stderr}")
        return False