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
    from icebreaker.pararellism.distribute import distribute_step_inputs
    from icebreaker.misc.time import time_run_update

    # Creates connection to allas
    print('Storage parameters')
    swift_parameters = storage['swift']
    print('Setting up swift client')
    setup_swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )

    track_inputs = distribute_step_inputs(
        storage_client = setup_swift_client,
        storage = storage,
        integration = integration,
        processing = processing
    )

    time_storage_parameters = storage['time-storage']
    time_object_name = time_storage_parameters['object-name']
    time_name = 'global-distribution-step'
    end_time = t.time()
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
    return track_inputs

@dsl.component(
    base_image = "python:3.12.3",
    packages_to_install = [
        "icebreaker[swift, data, ray, pararellism] @ git+https://github.com/K123AsJ0k1/ice-mlops-mlch.git@main#subdirectory=applications/packages/icebreaker"
    ]
)
def cluster_orhestractor_step(
    storage: dict,
    integration: dict,
    processing: dict,
    track_data: str     
):
    import time as t
    import ast
    from icebreaker.swift.setup import swift_setup_client 
    from icebreaker.ray.setup import ray_download_job
    from icebreaker.ray.use import ray_get_clients, ray_parallel_submit, ray_parallel_wait, ray_store_logs
    from icebreaker.misc.time import time_run_update

    start_time = t.time()

    print('Storage parameters')
    swift_parameters = storage['swift']
    print('Setting up swift client')
    work_swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )
    
    cluster_name = 'default'
    track_data_list = ast.literal_eval(track_data)
    if 0 < len(track_data_list):
        code_storage = storage['code-storage']
        cluster_yamls = integration['cluster-yamls']
        print(f'Track has {len(track_data_list)} inputs')
        for step_data in track_data_list:
            cluster_step = step_data['cluster_step']
            cluster_name = step_data['cluster_name']
            cluster_inputs = step_data['cluster_input']
            print(f'Running track step {cluster_step} in cluster {cluster_name}')
            
            if cluster_step in processing:
                step_processing_parameters = processing[cluster_step]
                print('Step exists')
                if cluster_name in step_processing_parameters['cluster']:
                    cluster_parameters = step_processing_parameters['cluster']
                    
                    cluster_clients = ray_get_clients(
                        configured_clusters = cluster_yamls,
                        cluster_parameters = cluster_parameters,
                        cluster_filter = [
                            cluster_name
                        ]
                    ) 

                    cluster_job_runtime = cluster_parameters[cluster_name]['job']['runtime']
                    job_directory, job_requirements = ray_download_job(
                        storage_client = work_swift_client,
                        storage_parameters = code_storage,
                        ray_runtime = cluster_job_runtime
                    )
                    step_processing_parameters['cluster'][cluster_name]['job']['runtime']['working_dir'] = job_directory
                    step_processing_parameters['cluster'][cluster_name]['job']['runtime']['pip'] = job_requirements

                    cluster_job_ids = ray_parallel_submit(
                        cluster_clients = cluster_clients,
                        cluster_inputs = cluster_inputs,
                        step_parameters = step_processing_parameters
                    )
                    
                    job_logs = ray_parallel_wait(
                        cluster_job_ids = cluster_job_ids,
                        multi_loop_amount = integration['multi-loop-amount'],
                        multi_loop_wait = integration['multi-loop-wait'],
                        job_loop_amount = integration['job-loop-amount'],
                        job_loop_wait = integration['job-loop-wait']
                    )
                    
                    log_storage = storage['log-storage']
                    log_object_prefix = cluster_name + '-' + cluster_step
                    ray_store_logs(
                        storage_client = work_swift_client,
                        storage_parameters = log_storage,
                        job_directory = job_directory,
                        job_logs = job_logs,
                        object_prefix = log_object_prefix
                    )

    # Track metrics
    end_time = t.time()
    time_storage_parameters = storage['time-storage']
    time_object_name = time_storage_parameters['object-name']
    time_name = 'cluster-orhestractor-step-' + cluster_name 
    time_stored_1, time_index_1, time_name_1 = time_run_update(
        storage_client = work_swift_client,
        storage_parameters = time_storage_parameters,
        object_name = time_object_name,
        time_name = time_name,
        start_time = start_time,
        end_time = end_time,
        time_index = -1
    )
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
    
    with dsl.ParallelFor(global_distribution_task.output) as track_data:
        current_task = cluster_orhestractor_step(
            storage = storage,
            integration = integration,
            processing = processing,
            track_data = track_data
        )