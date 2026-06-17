from kfp import dsl

@dsl.component(
    base_image = "python:3.12.3",
    packages_to_install = [
        "icebreaker[swift, data, ray, pararellism] @ git+https://github.com/K123AsJ0k1/ice-mlops-mlch.git@main#subdirectory=applications/packages/icebreaker"
    ]
)
def cluster_setup_step(
    storage: dict,
    integration: dict
):
    import time as t
    start_time = t.time()

    from icebreaker.swift.setup import swift_setup_client 
    from icebreaker.objects.use import objects_store_data 
    from icebreaker.misc.time import time_run_update

    print('Storage parameters')
    swift_parameters = storage['swift']
    print('Setting up swift client')
    setup_swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )
    code_storage = storage['code-storage']
    cluster_name = integration['cluster-name']
    cluster_yamls = integration['cluster-yamls']
    object_name = cluster_name + '.pkl'
    print('Storing cluster yamls')
    store_status = objects_store_data(
        swift_client = setup_swift_client,
        storage_parameters = {
            'bucket-target': code_storage['bucket-target'],
            'bucket-prefix': code_storage['bucket-prefix'],
            'bucket-user': code_storage['bucket-user'],
            'object-name': 'mana',
            'object-serialization': 'pickle',
            'path-replacers': {
                'name': object_name
            },
            'path-names': [],
            'debug-prints': True,
            'lock-parameters': {},
            'lock-location': None,
            'overwrite': True
        },
        object_data = cluster_yamls,
        object_metadata = {}
    )
    
    end_time = t.time()

    time_storage_parameters = storage['time-storage']
    time_object_name = time_storage_parameters['object-name']
    time_name = 'cluster-setup-step-7' 
    time_stored_1, time_index_1, time_name_1 = time_run_update(
        storage_client = setup_swift_client,
        storage_parameters = time_storage_parameters,
        object_name = time_object_name,
        time_name = time_name,
        start_time = start_time,
        end_time = end_time,
        time_index = -1
    )
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    
@dsl.component(
    base_image = "python:3.12.3",
    packages_to_install = [
        "icebreaker[swift, data, ray, pararellism] @ git+https://github.com/K123AsJ0k1/ice-mlops-mlch.git@main#subdirectory=applications/packages/icebreaker"
    ]
)
def global_distribution_step(
    storage: dict,
    integration: dict,
    processing: dict 
) -> list:
    import time as t
    start_time = t.time()
    
    from icebreaker.swift.setup import swift_setup_client 
    from icebreaker.data.use import data_list_objects
    from icebreaker.pararellism.division import (
        division_formatted_clusters, 
        division_cluster_weights,
        division_load_balanced_cluster_round_robin
    )
    from icebreaker.ray.use import ray_get_clients
    from icebreaker.misc.time import time_run_update
    
    # Creates connection to allas
    print('Storage parameters')
    swift_parameters = storage['swift']
    print('Setting up swift client')
    setup_swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )

    cluster_yamls = integration['cluster-yamls']
    cluster_priority = integration['cluster-priority']
    workflow_steps = integration['workflow-steps']
    resource_weights = integration['resource-weights']
    data_storage = storage['data-storage']
    skew_factor = integration['skew-factor']
    min_batch_size = integration['min-batch-size']
    global_inputs = []
    if 0 < len(workflow_steps):
        for step_key in workflow_steps:
            print(step_key)
            step_processing_parameters = processing[step_key]
            step_cluster_parameters = step_processing_parameters['cluster']
            cluster_clients = ray_get_clients(
                configured_clusters = cluster_yamls,
                cluster_parameters = step_cluster_parameters
            )
            print(cluster_clients)
            formatted_clusters = division_formatted_clusters(
                ray_clusters = cluster_clients
            )
            print(cluster_priority)
            cluster_weights = division_cluster_weights(
                resource_weights = resource_weights,
                formatted_clusters = formatted_clusters,
                cluster_priorities = cluster_priority,
                skew_factor = skew_factor
            )
            print(cluster_weights)

            object_prefix = processing[step_key]['general']['data-storage']['object-prefix']
            dataset_tuple_list = data_list_objects(
                storage_client = setup_swift_client,
                storage_parameters = data_storage,
                object_prefix = object_prefix
            )

            cluster_division = division_load_balanced_cluster_round_robin(
                target_list = dataset_tuple_list,
                cluster_weights = cluster_weights,
                min_batch_size = min_batch_size
            )
            step_inputs = []
            for cluster_name, cluster_input in cluster_division.items():
                print(f'{cluster_name} given batch input size {str(len(cluster_input))}')
                step_inputs.append({
                    'cluster_name': cluster_name,
                    'cluster_input': cluster_input
                })
            global_inputs.append(step_inputs)




    '''
    cluster_yamls = integration['cluster-yamls']
    cluster_priority = integration['cluster-priority']
    print(cluster_priority)
    cluster_clients = ray_get_clients(
        configured_clusters = cluster_yamls,
        cluster_parameters = cluster_priority 
    )

    print(cluster_clients)
    global_inputs = []
    if 0 < len(cluster_clients):
        print('Creating a cluster data distribution')
        formatted_clusters = division_formatted_clusters(
            ray_clusters = cluster_clients
        )
        print(formatted_clusters)
        cluster_weights = division_cluster_weights(
            resource_weights = integration['resource-weights'],
            formatted_clusters = formatted_clusters,
            cluster_priorities = cluster_priority 
        )
        print(cluster_weights)
        data_storage = storage['data-storage']
        for step_key in integration['workflow-steps']:
            print(step_key)
            object_prefix = processing[step_key]['general']['data-storage']['object-prefix']
            dataset_tuple_list = data_list_objects(
                storage_client = setup_swift_client,
                storage_parameters = data_storage,
                object_prefix = object_prefix
            )

            cluster_division = division_load_balanced_cluster_round_robin(
                target_list = dataset_tuple_list,
                cluster_weights = cluster_weights
            )
            step_inputs = []
            for cluster_name, cluster_input in cluster_division.items():
                step_inputs.append({
                    'cluster_name': cluster_name,
                    'cluster_input': cluster_input
                })
            global_inputs.append(step_inputs)
    '''

    end_time = t.time()
    '''
    time_storage_parameters = storage['time-storage']
    time_object_name = time_storage_parameters['object-name']
    time_name = 'global-distribution-step'
    time_stored_1, time_index_1, time_name_1 = time_run_update(
        storage_client = setup_swift_client,
        storage_parameters = time_storage_parameters,
        object_name = time_object_name,
        time_name = time_name,
        start_time = start_time,
        end_time = end_time,
        time_index = -1
    )
    '''
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return global_inputs

@dsl.component(
    base_image = "python:3.12.3",
    packages_to_install = [
        "icebreaker[swift, data, ray, pararellism] @ git+https://github.com/K123AsJ0k1/ice-mlops-mlch.git@main#subdirectory=applications/packages/icebreaker"
    ]
)
def single_cluster_step(
    storage: dict,
    integration: dict,
    processing: dict,
    step_key: str,
    target_cluster: str,   
    cluster_input: list      
):
    import time as t
    from icebreaker.swift.setup import swift_setup_client 
    from icebreaker.ray.setup import ray_download_job
    from icebreaker.ray.use import ray_get_clients, ray_store_logs
    from ray.job_submission import JobSubmissionClient, JobStatus
    
    start_time = t.time()

    print(step_key)
    print(target_cluster)
    print(cluster_input)
    '''
    setup_swift_client = swift_setup_client(swift_parameters=storage['swift'])
    
    step_processing_parameters = processing[step_key]
    cluster_key = f"{target_cluster_env}-{target_cluster_name}"
    
    # 1. Connect ONLY to this specific target cluster
    cluster_clients = ray_get_clients(
        configured_clusters=integration['cluster-yamls'],
        cluster_parameters={target_cluster_name: step_processing_parameters['cluster'][target_cluster_name]}
    )
    
    cluster_client = cluster_clients[target_cluster_env]['clusters'][target_cluster_name]['client']
    
    # 2. Prepare Environment 
    cluster_job_runtime = step_processing_parameters['cluster'][target_cluster_name]['job']['runtime']
    job_directory, job_requirements = ray_download_job(
        storage_client=setup_swift_client,
        storage_parameters=storage['code-storage'],
        ray_runtime=cluster_job_runtime
    )
    step_processing_parameters['cluster'][target_cluster_name]['job']['runtime']['working_dir'] = job_directory
    step_processing_parameters['cluster'][target_cluster_name]['job']['runtime']['pip'] = job_requirements

    # 3. Submit single job
    if len(assigned_datasets) > 0:
        # Reconstruct parameters for the internal ray runner logic
        # Pass a dictionary pretending this cluster is the only one available
        cluster_inputs = {cluster_key: assigned_datasets}
        
        # Re-use your parameter-building helper
        used_parameters = ray_input_parameters(
            cluster_name=cluster_key,
            cluster_inputs=cluster_inputs,
            step_parameters=step_processing_parameters
        )
        
        # Submit directly to the specific cluster client
        job_id = ray_submit_job(
            ray_client=cluster_client,
            ray_parameters=used_parameters,    
            ray_job_file=used_parameters['job']['main-file'],
            ray_runtime=used_parameters['job']['runtime']
        )
        print(f"Submitted Job {job_id} to cluster {cluster_key}")
        
        # 4. Wait ONLY for this cluster's job
        waited_job_status = [JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.STOPPED]
        
        # Simplified clean wait-loop for a single job
        for _ in range(integration['multi-loop-amount']):
            job_status, job_logs = ray_wait_job(
                ray_client=cluster_client,
                ray_waited_status=waited_job_status,
                ray_job_id=job_id, 
                job_loop_amount=integration['job-loop-amount'],
                job_loop_wait=integration['job-loop-wait'],
                status_print=False
            )
            if job_status in waited_job_status:
                break
            t.sleep(integration['multi-loop-wait'])
            
        # 5. Handle Logs
        log_object_prefix = f"{cluster_key}-{step_key}"
        ray_store_logs(
            storage_client=setup_swift_client,
            storage_parameters=storage['log-storage'],
            job_directory=job_directory,
            job_logs={job_id: {'status': job_status.value, 'logs': job_logs}},
            object_prefix=log_object_prefix
        )
    '''
    # Track metrics
    end_time = t.time()
    '''
    time_storage_parameters = storage['time-storage']
    time_object_name = time_storage_parameters['object-name']
    time_name = 'multi-submission-' + step_key 
    time_stored_1, time_index_1, time_name_1 = time_run_update(
        storage_client = setup_swift_client,
        storage_parameters = time_storage_parameters,
        object_name = time_object_name,
        time_name = time_name,
        start_time = start_time,
        end_time = end_time,
        time_index = -1
    )
    '''
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    
@dsl.pipeline(
    name = "data-analysis-parallel-pipeline",
    description = "Internal and external data analysis"
)
def data_analysis_parallel_pipeline(
    storage: dict,
    integration: dict,
    processing: dict
):
    global_distribution_task = global_distribution_step(
        storage = storage,
        integration = integration,
        processing = processing
    )

    #previous_task = global_distribution_task
    #with dsl.ParallelFor(global_distribution_task.output) as item:
    #    current_task = single_cluster_step(
    #        storage = storage,
    #        integration = integration,
    #        processing = processing,
    #        step_key = step_key,
    #        target_cluster = cluster_name,   
    #        cluster_input = cluster_input[cluster_name]
    #    ).after(previous_task)
    #    previous_task = current_task
    
    # setup step
    #previous_task = global_distribution_task
    #for step_key in step_keys:
        #step_distribution = global_distribution_task.outputs[step_key]
        #for cluster_name, cluster_input in step_distribution.items():    
        #    current_task = single_cluster_step(
        #        storage = storage,
        #        integration = integration,
        #        processing = processing,
        #        step_key = step_key,
        #        target_cluster = cluster_name,   
        #        cluster_input = cluster_input[cluster_name]
        #    ).after(previous_task)
        #    previous_task = current_task