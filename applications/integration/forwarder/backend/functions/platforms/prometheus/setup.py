import os
import shutil
from prometheus_client import CollectorRegistry, multiprocess, start_http_server

def prometheus_create_server():
    # This works, but each time that 
    # the backend is restarted the 
    # gauge db is recreated. This means 
    # that the metrics can be recollected
    # which is why the set prometheus 
    # directory should be cleaned at restart 

    prometheus_directory = os.environ.get('PROMETHEUS_MULTIPROC_DIR')
    
    if os.path.exists(prometheus_directory):
        shutil.rmtree(prometheus_directory)
   
    os.makedirs(prometheus_directory, exist_ok=True)
    
    wanted_port = int(os.environ.get('PROMETHEUS_PORT'))

    global_registry = CollectorRegistry() 
    multiprocess.MultiProcessCollector(global_registry)
    start_http_server(
        port = wanted_port, 
        registry = global_registry
    ) 