import airflow_client.client
import requests
from pydantic import BaseModel
import os

class Token(BaseModel):
    access_token: str
# consider refactoring later
def airflow_get_token(
    host: str,
    username: str,
    password: str,
) -> any:        
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
    response_success = Token(**response.json())
    return response_success.access_token

def airflow_setup_configuration() -> any:
    airflow_host = os.environ.get('AIRFLOW_HOST')
    airflow_username = os.environ.get('AIRFLOW_USERNAME')
    airflow_password = os.environ.get('AIRFLOW_PASSWORD')

    configuration = airflow_client.client.Configuration(
        host = airflow_host
    )
    configuration.access_token = airflow_get_token(
        host = airflow_host,
        username = airflow_username,
        password = airflow_password
    )
    return configuration 