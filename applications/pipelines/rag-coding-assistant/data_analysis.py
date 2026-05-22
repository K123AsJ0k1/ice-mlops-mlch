from kfp import dsl
 
@dsl.component(
    base_image = "python:3.12.3",
    packages_to_install = [
        "icebreaker[swift, ray, pararellism] @ git+https://github.com/K123AsJ0k1/ice-mlops-mlch.git@main#subdirectory=applications/packages/icebreaker"
    ]
)
def multi_submission_step(
    storage_parameters: dict,
    integration_parameters: dict,
    process_parameters: dict,
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
    
    # Creates connection to allas
    print('Storage parameters')
    swift_parameters = storage_parameters['swift-parameters']
    print('Setting up swift client')
    setup_swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )
    print('Swift client setup')
    local_cloud_cluster_yamls = integration_parameters['cluster-yamls']
    cluster_parameters = process_parameters[step_key]['cluster-parameters']
    
    # Checks what clusters are available and then divides the work
    cluster_clients = ray_get_clients(
        configured_clusters = local_cloud_cluster_yamls,
        cluster_parameters = cluster_parameters
    )
    print(cluster_clients)
    if 0 < len(cluster_clients):
        print('Clusters available')
        code_storage = storage_parameters['code-storage']
        
        for cluster, details in cluster_parameters.items():
            cluster_job_runtime = details['job']['runtime']
            job_directory, job_requirements = ray_download_job(
                storage_client = setup_swift_client,
                storage_parameters = code_storage,
                ray_runtime = cluster_job_runtime
            )
            cluster_parameters[cluster]['job']['runtime']['working_dir'] = job_directory
            cluster_parameters[cluster]['job']['runtime']['pip'] = job_requirements
        
        # Splits the work
        print('Creating a cluster data distribution')
        formatted_clusters = division_formatted_clusters(
            ray_clusters = cluster_clients
        )
        print(formatted_clusters)
        local_cloud_resource_weights = integration_parameters['resource-weights']
        local_cloud_cluster_weights = division_cluster_weights(
            resource_weights = local_cloud_resource_weights,
            formatted_clusters = formatted_clusters
        )

        print(local_cloud_cluster_weights)
        if 0 < len(local_cloud_cluster_weights):
            data_storage = storage_parameters['data-storage']
            object_prefix = cluster_parameters['general-parameters']['storage']['data-storage']['object-prefix']
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
                cluster_parameters = cluster_parameters
            )

            job_logs = ray_multi_wait(
                cluster_job_ids = cluster_job_ids,
                amount_of_loops = 100,
                loop_wait = 5
            )
            
            log_storage = storage_parameters['log-storage']
            ray_store_logs(
                storage_client = setup_swift_client,
                storage_parameters = log_storage,
                job_directory = job_directory,
                job_logs = job_logs
            )
                
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)

@dsl.pipeline(
    name = "data-analysis-pipeline",
    description = "Internal and external data analysis"
)
def data_analysis_pipeline(
    storage_parameters: dict,
    integration_parameters: dict,
    process_parameters: dict
):
    task_1 = multi_submission_step(
        storage_parameters = storage_parameters,
        integration_parameters = integration_parameters,
        process_parameters = process_parameters,
        step_key = 'step-1'
    )

    #task_2 = multi_submission_step(
    #    storage_parameters = storage_parameters,
    #    integration_parameters = integration_parameters
    #).after(task_1)
    
    
    