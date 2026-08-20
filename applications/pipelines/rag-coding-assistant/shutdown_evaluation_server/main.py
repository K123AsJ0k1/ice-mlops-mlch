import sys
from importlib.metadata import version
from ray import serve

def shutdown_evaluation_server():
    try:   
        serve.delete(name = 'model_evaluation_server') 
        return True
    except Exception as e:
        print(f'Serve shutdown: {e}')
        return False 

if __name__ == "__main__":
    print('Starting ray job')
    print('Python version is:' + str(sys.version))
    check_packages = [
        'ray',
    ]
   
    for pkg_name in check_packages:
        try:
            print(f'{pkg_name} version is {version(pkg_name)}')
        except Exception as e:
            print(f'package not found error {e}')

    print('Running Serve shutdown')
    job_output = shutdown_evaluation_server()
    print('job success:' + str(job_output))

    print('Ray job Complete')