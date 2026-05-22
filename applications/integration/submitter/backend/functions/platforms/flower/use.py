import os
import requests
from requests.auth import HTTPBasicAuth
 
def flower_get_tasks() -> any:
    flower_address = os.environ.get('FLOWER_ENDPOINT')
    flower_port = os.environ.get('FLOWER_PORT')
    flower_username = os.environ.get('FLOWER_USERNAME')
    flower_password = os.environ.get('FLOWER_PASSWORD')
    
    flower_url = 'http://' + flower_address + ':' + flower_port + '/api/tasks'
    response = requests.get(
        url = flower_url, 
        auth = HTTPBasicAuth(
            username = flower_username, 
            password = flower_password
        )
    )
    tasks = {}
    if response.status_code == 200:
        tasks = response.json()
    return tasks
