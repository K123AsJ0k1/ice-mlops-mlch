import sys
from importlib.metadata import version
from ray import serve

def serve_shutdown():
    try:   
        serve.shutdown()    
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
    testing_data_output = serve_shutdown()
    print('Testing success:' + str(testing_data_output))

    print('Ray job Complete')