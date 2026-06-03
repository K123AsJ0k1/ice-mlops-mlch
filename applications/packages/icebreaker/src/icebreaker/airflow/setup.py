
def airflow_get_token(
    host: str,
    username: str,
    password: str,
) -> any:   
    try:
        import requests
        from pydantic import BaseModel 
    except ImportError as e:
        raise ImportError("airflow/setup failed to import", e)

    url = f"{host}/auth/token"
    payload = {
        "username": username,
        "password": password,
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(
        url, 
        json = payload, 
        headers = headers
    )
    if response.status_code != 201:
        return None

    class Token(BaseModel):
        access_token: str

    response_success = Token(**response.json())
    return response_success.access_token

def airflow_setup_configuration(
    airflow_host: str,
    airflow_username: str,
    airflow_password: str
) -> any:
    try:
        from airflow_client.client import Configuration
    except ImportError as e:
        raise ImportError("airflow/setup failed to import", e)

    configuration = Configuration(
        host = airflow_host
    )
    configuration.access_token = airflow_get_token(
        host = airflow_host,
        username = airflow_username,
        password = airflow_password
    )
    return configuration 

def airflow_create_connections(
    secret_file: str,
    compose_file: str
): 
    try:
        import os
        import yaml
        import json
    except ImportError as e:
        raise ImportError("airflow/setup failed to import", e)
    
    airflow_connections = []
    if not os.path.exists(secret_file):
        print(f"Secret file not found at {secret_file}")
        return airflow_connections
    
    if not os.path.exists(compose_file):
        print(f"Compose file not found at {compose_file}")
        return airflow_connections
    
    secret_dict = None
    with open(secret_file, 'r') as f:
        secret_dict = yaml.safe_load(f)

    secret_platforms = secret_dict['platforms']
    secret_connections = secret_dict['connections']
    
    for p_type, values in secret_platforms.items():
        for name, parameters  in values.items():
            connection_type = parameters['type']
            if connection_type == 'ssh':
                connection_host = parameters['address']
                connection_user = parameters['user']
                connection_key = parameters['key']
                key_parameters = secret_connections[connection_type][connection_key]
                connection_path = key_parameters['path']
                connection_phrase = key_parameters['phrase']
                connection_id = p_type + '-' + name

                values = {
                    'conn_type': 'ssh',
                    'login': connection_user,
                    'password': connection_phrase,
                    'host': connection_host,
                    'port': 22,
                    'extra': {
                        'key_file': connection_path
                    }
                }
    
                compose_command = "-f " + os.path.abspath(compose_file)
                connection_name = "'" + connection_id + "'"
                connection_json = "'" + json.dumps(values) + "'"
                cli_command = [
                    "docker", 
                    "compose", 
                    compose_command,
                    "run", 
                    "airflow-worker",
                    "airflow", 
                    "connections", 
                    "add",
                    connection_name,
                    "--conn-json",
                    connection_json
                ]
            
                airflow_connections.append(' '.join(cli_command))
    return airflow_connections

def airflow_apply_connections(
    connection_commands: list
):
    try:
        from ..sub_pcs.use import subprocess_run_command
    except ImportError as e:
        raise ImportError("airflow/setup failed to import", e)

    # For some reason there might be empty runs for the first command
    # This can be fixed by running the missing commands as is
    print_results = []
    for connection_command in connection_commands:
        result_print, error_print = subprocess_run_command(
            command = connection_command
        )
        print_results.append(result_print)
    
    return print_results