import os
import sys
import ray
import re
import time
import json
from importlib.metadata import version
from ray import serve

def llama_test(
    job_parameters: dict
):
    try:
        serve_parameters = job_parameters['serve']
        serve_host = serve_parameters['host']
        serve_port = serve_parameters['port']
        serve_shutdown = serve_parameters['shutdown']
        serve_time = serve_parameters['time']

        model_parameters = job_parameters['model']
        generator_model_parmaters = model_parameters['generator-model-parameters']

        if generator_model_parmaters['inference'] == 'llama':
            print('Setting up LLAMA inference')
            try:
                from servers.llama_generator import LLAMA_Generator
            except ImportError as e:
                raise ImportError("generator/ failed to import", e)

            serve.start(
                http_options = {
                    'host': serve_host,
                    'port': serve_port
                }
            )

            serve.run(
                LLAMA_Generator.bind(
                    model_parameters = generator_model_parmaters
                ), 
                name = 'llama_server', 
                route_prefix='/'
            )   
        
        if serve_shutdown:
            time.sleep(serve_time)    
            serve.shutdown()  
        return True
    except Exception as e:
        print(f'llama error {e}')
        return False 

if __name__ == "__main__":
    print('Starting ray job')
    print('Python version is:' + str(sys.version))
    check_packages = [
        'ray',
        'fastapi',
        'llama-cpp-python',
        'huggingface-hub',
        'jinja2'
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