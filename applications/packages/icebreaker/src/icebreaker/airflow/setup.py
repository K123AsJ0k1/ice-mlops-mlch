
def airflow_get_token(
    host: str,
    username: str,
    password: str,
) -> any:   
    try:
        import requests
        from pydantic import BaseModel 
    except ImportError as e:
        raise ImportError("Failed to import", e)

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
        raise ImportError("Failed to import", e)

    configuration = Configuration(
        host = airflow_host
    )
    configuration.access_token = airflow_get_token(
        host = airflow_host,
        username = airflow_username,
        password = airflow_password
    )
    return configuration 
