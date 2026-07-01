import os
import sys
import ray
import re
import time
import json
from importlib.metadata import version
from fastapi import FastAPI
from ray import serve

app = FastAPI()

@serve.deployment
@serve.ingress(app)
class Test_Server:
    @app.get("/output")
    async def output_route(
        self
    ):
        return {"status": "success", "message": "FastApi-RayServe Hello World"}

def llama_test(
    job_parameters: dict
):
    try:
        serve_parameters = job_parameters['serve']
        serve_host = serve_parameters['host']
        serve_port = serve_parameters['port']

        serve.start(
            http_options = {
                'host': serve_host,
                'port': serve_port
            }
        )

        serve.run(
            Test_Server.bind(), 
            name = 'test_server', 
            route_prefix='/'
        )   
        return True
    except Exception as e:
        print(f'llama error {e}')
        return False 

if __name__ == "__main__":
    print('Starting ray job')
    print('Python version is:' + str(sys.version))
    check_packages = [
        'ray',
        'fastapi'
    ]
   
    for pkg_name in check_packages:
        try:
            print(f'{pkg_name} version is {version(pkg_name)}')
        except Exception as e:
            print(f'package not found error {e}')

    print('Getting input')
    job_parameters = json.loads(sys.argv[1])

    print('Running llama test')
    testing_data_output = llama_test(
        job_parameters = job_parameters
    )
    print('Testing success:' + str(testing_data_output))

    print('Ray job Complete')