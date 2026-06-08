import requests
from requests.auth import HTTPBasicAuth
 
def flower_get_tasks(
    flower_address: str,
    flower_port: str,
    flower_username: str,
    flower_password: str
) -> any:
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
