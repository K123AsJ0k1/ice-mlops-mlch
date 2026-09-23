import os
import sys
import ray
import re
import time
import json
from importlib.metadata import version
from ray import serve

def llama_cpp_server(
    job_parameters: dict
):
    try:
        serve_parameters = job_parameters['serve']
        serve_id = serve_parameters['id']
        serve_host = serve_parameters['host']
        serve_port = serve_parameters['port']
        serve_shutdown = serve_parameters['shutdown']
        serve_time = serve_parameters['time']
        serve_instance_name = serve_parameters['name']
        serve_route_prefix = serve_parameters['prefix']

        model_parameters = job_parameters['model']
        generator_model_parmaters = model_parameters['generator-model-parameters']
        generator_model_parmaters['serve-id'] = serve_id
        
        if generator_model_parmaters['inference'] == 'llama':
            print('Setting up LLAMA inference')
            try:
                from servers.llama_cpp_generator import LLAMA_CPP_GENERATOR
            except ImportError as e:
                raise ImportError("Failed to import LLAMA_CPP_GENERATOR", e)
 
            serve.start(
                http_options = {
                    'host': serve_host,
                    'port': serve_port
                }
            ) 
 
            serve.run(
                LLAMA_CPP_GENERATOR.bind(
                    model_parameters = generator_model_parmaters
                ), 
                name = serve_instance_name, 
                route_prefix = serve_route_prefix
            )   
        
        if serve_shutdown:
            time.sleep(serve_time)    
            serve.shutdown()  
        return True
    except Exception as e:
        print(f'llama cpp server error: {e}')
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

    print('Running llama.cpp server')
    output = llama_cpp_server(
        job_parameters = job_parameters
    )
    print('Setup success:' + str(output))

    print('Ray job Complete')