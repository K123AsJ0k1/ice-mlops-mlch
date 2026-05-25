def ray_submit_job(
    ray_client: any,
    ray_parameters: any,
    ray_job_file: any,
    ray_runtime: any
) -> any:
    try:
        import json
    except ImportError as e:
        raise ImportError("Failed to import", e)

    command = "python " + str(ray_job_file)
    if 0 < len(ray_parameters):
        command = command + " '" + json.dumps(ray_parameters) + "'"
    job_id = ray_client.submit_job(
        entrypoint = command,
        runtime_env = ray_runtime
    )
    return job_id
 
def ray_wait_job(
    ray_client: any,
    ray_waited_status: list,
    ray_job_id: int, 
    loop_timeout: int,
    wait_timeout: int,
    status_print: bool
) -> any:
    try:
        import time as t
    except ImportError as e:
        raise ImportError("Failed to import", e)

    start = t.time()
    job_status = None
    job_logs = None
    while t.time() - start <= loop_timeout:
        status = ray_client.get_job_status(ray_job_id)
        if status_print:
            print(f"status: {status}")
        if status in ray_waited_status:
            job_status = status
            job_logs = ray_client.get_job_logs(ray_job_id)
            break
        t.sleep(wait_timeout)
    return job_status, job_logs

def ray_serve_route(
    route_address: str,
    route_path: str,
    route_type: str,
    route_input: any,
    timeout: any
) -> any:
    try:
        import requests
        import json
    except ImportError as e:
        raise ImportError("Failed to import", e)

    full_url = 'http://' + route_address + route_path
    print(full_url)
    if route_type == 'POST':
        route_response = requests.post(
            url = full_url,
            json = route_input
        )
    if route_type == 'GET':
        route_response = requests.get(
            url = full_url
        )

    route_status_code = None
    route_returned_text = {}
    if not route_response is None:
        route_status_code = route_response.status_code
        if route_status_code == 200:
            route_returned_text = json.loads(route_response.text)
    return route_status_code, route_returned_text

def ray_get_clients(
    configured_clusters: any,
    cluster_parameters: any
) -> any:
    try:
        from .setup import ray_setup_client
        from ..misc.dict import create_nested_dict
    except ImportError as e:
        raise ImportError("Failed to import", e)
    
    cluster_clients = {}
    for env, env_config in configured_clusters.items():
        env_clusters = env_config['clusters']
        for env_cluster, details in env_clusters.items():
            targeted_cluster = env + '-' + env_cluster
            if targeted_cluster in cluster_parameters:
                kubernetes_dash_address = details['network']['kubernetes']['dash'] 
                cluster_ray_client = ray_setup_client(
                    dashboard_address = kubernetes_dash_address,
                    loop_timeout = 1,
                    test_timeout = 1,
                    wait_timeout = 1
                )
                if cluster_ray_client is None:
                    print('Cluster', env, env_cluster, kubernetes_dash_address, 'was not found') 
                else:
                    print('Cluster', env, env_cluster, kubernetes_dash_address, 'was found')
                    if not env in env_clusters:
                        used_path = env + '-clusters-' + env_cluster
                        cluster_clients = create_nested_dict(
                            target_dict = cluster_clients,
                            key_path = used_path,
                            separator = '-'
                        )
                    cluster_clients[env]['clusters'][env_cluster] = details
                    cluster_clients[env]['clusters'][env_cluster]['client'] = cluster_ray_client
    return cluster_clients

def ray_input_parameters(
    cluster_name: any,
    cluster_inputs: any,
    step_parameters: any
) -> any:
    try:
        import copy
    except ImportError as e:
        raise ImportError("Failed to import", e)
    input_parameters = {}
    for cluster_key, input in cluster_inputs.items():
        if cluster_name in cluster_key:
            input_parameters = copy.deepcopy(step_parameters['cluster'][cluster_name])  
            template_parameters = copy.deepcopy(step_parameters['general'])
            
            for param_key in template_parameters.keys():
                if 'data' in param_key:
                    template_parameters[param_key]['input'] = cluster_inputs[cluster_key]
            
            input_parameters.update(template_parameters)
            break
    return input_parameters
            
def ray_multi_submit(
    cluster_clients: any,
    cluster_inputs: any,
    step_parameters: any
) -> list:
    cluster_job_ids = []

    for env, env_details in cluster_clients.items():
        clusters = env_details['clusters']
        for env_cluster, cluster_details in clusters.items():
            cluster_client = cluster_details['client']
            targeted_cluster = env + '-' + env_cluster
            used_parameters = ray_input_parameters(
                cluster_name = targeted_cluster,
                cluster_inputs = cluster_inputs,
                step_parameters = step_parameters
            )

            if 0 < len(used_parameters):
                used_job_file = used_parameters['job']['main-file']
                used_runtime = used_parameters['job']['runtime']
                
                cluster_job_id = ray_submit_job(
                    ray_client = cluster_client,
                    ray_parameters = used_parameters,    
                    ray_job_file = used_job_file,
                    ray_runtime = used_runtime
                )
                print('Submitted job ', used_job_file, ' into cluster ', targeted_cluster)
                cluster_job_ids.append((cluster_client, cluster_job_id))
    return cluster_job_ids

def ray_multi_wait(
    cluster_job_ids: any,
    amount_of_loops: int,
    loop_wait: int
):
    try:
        import time as t
        from ray.job_submission import JobStatus
    except ImportError as e:
        raise ImportError("Failed to import", e)
    
    monitored_jobs = list(cluster_job_ids)
    collected_logs = {}

    waited_job_status = [
        JobStatus.SUCCEEDED,
        JobStatus.FAILED,
        JobStatus.STOPPED
    ]

    for round in range(amount_of_loops):
        if not monitored_jobs:
            break

        for item in list(monitored_jobs):
            cluster_client, job_id = item 
            
            job_status, job_logs = ray_wait_job(
                ray_client = cluster_client,
                ray_waited_status = waited_job_status,
                ray_job_id = job_id, 
                loop_timeout = 5,
                wait_timeout = 5,
                status_print = False
            )

            if job_status in waited_job_status:
                collected_logs[job_id] = {
                    'status': job_status.value,
                    'logs': job_logs
                }
                monitored_jobs.remove(item)
            
        t.sleep(loop_wait)
    return collected_logs

def ray_store_logs(
    storage_client: any,
    storage_parameters: any,
    job_directory: str,
    job_logs: any
):
    try:
        import os
        import pickle
        import time as t
        from ..storage.management import object_storage_interaction
    except ImportError as e:
        raise ImportError("Failed to import", e)

    if 0 < len(job_logs):
        directory_name = job_directory.split('/')[-1]
        for job_id, data in job_logs.items():
            stored_metadata = {'version': 1}
            formatted_data = pickle.dumps(data)
            object_name = job_id + '.pkl'
            object_stored = object_storage_interaction(
                storage_client = storage_client,
                lock_parameters = {},
                lock_location = 'no-lock',
                parameters = {
                    'mode': 'send',
                    'bucket-target': storage_parameters['bucket-target'],
                    'bucket-prefix': storage_parameters['bucket-prefix'],
                    'bucket-user': storage_parameters['bucket-user'],
                    'object-name': 'logs',
                    'path-replacers': {
                        'name': 'RAY'
                    },
                    'path-names': [
                        directory_name,
                        object_name
                    ],
                    'overwrite': True,
                    'debug-prints': True
                },
                object_data = formatted_data,
                object_metadata = stored_metadata
            ) 