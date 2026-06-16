from kfp import dsl

@dsl.component(
    base_image = "python:3.12.3",
    packages_to_install = [
        "icebreaker[swift_client, data, ray, pararellism] @ git+https://github.com/K123AsJ0k1/ice-mlops-mlch.git@main#subdirectory=applications/packages/icebreaker"
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
        "icebreaker[swift_client, data, ray, pararellism] @ git+https://github.com/K123AsJ0k1/ice-mlops-mlch.git@main#subdirectory=applications/packages/icebreaker"
    ]
)
def multi_submission_step(
    storage: dict,
    integration: dict,
    processing: dict,
    step_key: str
):
    import time as t
    start_time = t.time()
    
    from icebreaker.swift.setup import swift_setup_client 
    from icebreaker.data.use import data_list_objects
    from icebreaker.pararellism.division import (
        division_formatted_clusters, 
        division_cluster_weights,
        division_load_balanced_cluster_round_robin
    )
    from icebreaker.ray.setup import ray_download_job
    from icebreaker.ray.use import (
        ray_get_clients,
        ray_multi_submit,
        ray_multi_wait,
        ray_store_logs
    )
    from icebreaker.misc.time import time_run_update
    
    # Creates connection to allas
    print('Storage parameters')
    swift_parameters = storage['swift']
    print('Setting up swift client')
    setup_swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )
    print('Swift client setup')
    local_cloud_cluster_yamls = integration['cluster-yamls']
    step_processing_parameters = processing[step_key]
    step_general_parameters = step_processing_parameters['general']
    step_cluster_parameters = step_processing_parameters['cluster']
    
    # Checks what clusters are available and then divides the work
    cluster_clients = ray_get_clients(
        configured_clusters = local_cloud_cluster_yamls,
        cluster_parameters = step_cluster_parameters
    )
    print(cluster_clients)
    if 0 < len(cluster_clients):
        print('Clusters available')
        code_storage = storage['code-storage']
        
        for cluster, details in step_cluster_parameters.items():
            cluster_job_runtime = details['job']['runtime']
            # remove the need to download the same files
            job_directory, job_requirements = ray_download_job(
                storage_client = setup_swift_client,
                storage_parameters = code_storage,
                ray_runtime = cluster_job_runtime
            )
            step_processing_parameters['cluster'][cluster]['job']['runtime']['working_dir'] = job_directory
            step_processing_parameters['cluster'][cluster]['job']['runtime']['pip'] = job_requirements
        
        # Splits the work
        print('Creating a cluster data distribution')
        formatted_clusters = division_formatted_clusters(
            ray_clusters = cluster_clients
        )
        print(formatted_clusters)
        local_cloud_resource_weights = integration['resource-weights']
        local_cloud_cluster_weights = division_cluster_weights(
            resource_weights = local_cloud_resource_weights,
            formatted_clusters = formatted_clusters
        )

        print(local_cloud_cluster_weights)
        if 0 < len(local_cloud_cluster_weights):
            data_storage = storage['data-storage']
            object_prefix = step_general_parameters['data-storage']['object-prefix']
            dataset_tuple_list = data_list_objects(
                storage_client = setup_swift_client,
                storage_parameters = data_storage,
                object_prefix = object_prefix
            )
            # This is affected by the order the input sets
            print('Dividing data')
            clustered_dataset_paths = division_load_balanced_cluster_round_robin(
                target_list = dataset_tuple_list,
                cluster_weights = local_cloud_cluster_weights
            )

            cluster_job_ids = ray_multi_submit(
                cluster_clients = cluster_clients,
                cluster_inputs = clustered_dataset_paths,
                step_parameters = step_processing_parameters
            )
            
            job_logs = ray_multi_wait(
                cluster_job_ids = cluster_job_ids,
                multi_loop_amount = integration['multi-loop-amount'],
                multi_loop_wait = integration['multi-loop-wait'],
                job_loop_amount = integration['job-loop-amount'],
                job_loop_wait = integration['job-loop-wait']
            )
            # Maybe also give cluster name to the log
            log_storage = storage['log-storage']
            cluster_name = integration['cluster-name']
            log_object_prefix = cluster_name + '-' + step_key
            ray_store_logs(
                storage_client = setup_swift_client,
                storage_parameters = log_storage,
                job_directory = job_directory,
                job_logs = job_logs,
                object_prefix = log_object_prefix
            )
                
    end_time = t.time()
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
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)

@dsl.pipeline(
    name = "preprocess-pipeline",
    description = "RAG, evalution and validation dataset processing"
)
def data_preprocess_pipeline(
    storage: dict,
    integration: dict,
    processing: dict
):
    # First, use external datasets to create 8000 row evalution dataset
    # This should all the parquet data, divide it between all the clusters to get n row dataset
    # Success
    task_1 = multi_submission_step(
        storage = storage,
        integration = integration,
        processing = processing,
        step_key = 'step-1'
    )
    '''
    # Success
    task_2 = cluster_setup_step(
        storage = storage,
        integration = integration
    ).after(task_2)
    # Second, use internal datasets with a LLM to create 2000 row syntehtic validation dataset
    task_3 = multi_submission_step(
        storage = storage,
        integration = integration,
        processing = processing,
        step_key = 'step-2'
    )
    # Finally, use internal datasets to provide data into the RAG vector database
    task_4 = multi_submission_step(
        storage = storage,
        integration = integration,
        processing = processing,
        step_key = 'step-3'
    )
    '''
    
    
    
    
    
    #task_1 = rag_dataset_processing(
    #    storage_parameters = storage_parameters,
    #    integration_parameters = integration_parameters
    #)

    #task_2 = evaluation_dataset_processing(
    #    storage_parameters = storage_parameters,
    #    integration_parameters = integration_parameters
    #).after(task_1)

    #task_3 = validation_dataset_processing(
    #    storage_parameters = storage_parameters,
    #    integration_parameters = integration_parameters
    #).after(task_2)