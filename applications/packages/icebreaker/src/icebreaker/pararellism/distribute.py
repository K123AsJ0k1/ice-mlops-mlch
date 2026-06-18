def distribute_step_inputs(
    storage_client: any,
    storage: dict,
    integration: dict,
    processing: dict
):
    try:
        from ..ray.use import ray_get_clients
        from ..data.use import data_list_objects
        from ..pararellism.division import (
            division_formatted_clusters, 
            division_cluster_weights,
            division_load_balanced_cluster_round_robin
        )
    except ImportError as e:
        raise ImportError("pararellism/distribute to import", e)
    
    cluster_yamls = integration['cluster-yamls']
    cluster_priority = integration['cluster-priority']
    hardware_influence = integration['hardware-influence']
    workflow_steps = integration['workflow-steps']
    resource_weights = integration['resource-weights']
    data_storage = storage['data-storage']
    min_initial_inputs = integration['min-initial-inputs']
    min_batch_size = integration['min-batch-size']
    cluster_inputs = {}
    if 0 < len(workflow_steps):
        for step_key in workflow_steps:
            print(f'Distributing step {step_key}')
            step_processing_parameters = processing[step_key]
            step_cluster_parameters = step_processing_parameters['cluster']
            
            cluster_clients = ray_get_clients(
                configured_clusters = cluster_yamls,
                cluster_parameters = step_cluster_parameters,
                cluster_filter = []
            )
            
            formatted_clusters = division_formatted_clusters(
                ray_clusters = cluster_clients
            ) 

            cluster_weights = division_cluster_weights(
                resource_weights = resource_weights,
                formatted_clusters = formatted_clusters,
                cluster_priority_percentages = cluster_priority,
                hardware_influence = hardware_influence
            )
            
            object_prefix = processing[step_key]['general']['data-storage']['object-prefix']
            dataset_tuple_list = data_list_objects(
                storage_client = storage_client,
                storage_parameters = data_storage,
                object_prefix = object_prefix
            )

            cluster_division = division_load_balanced_cluster_round_robin(
                target_list = dataset_tuple_list,
                cluster_weights = cluster_weights,
                min_initial_inputs = min_initial_inputs,
                min_batch_size = min_batch_size
            )
        
            for cluster_name, cluster_input in cluster_division.items():
                print(f'{cluster_name} given batch input size {str(len(cluster_input))}')
                if not cluster_name in cluster_inputs:
                    cluster_inputs[cluster_name] = []

                cluster_inputs[cluster_name].append({
                    'cluster_step': step_key,
                    'cluster_name': cluster_name,
                    'cluster_input': cluster_input
                })
    track_inputs = []
    for used_name, step_inputs in cluster_inputs.items():
        track_inputs.append(step_inputs)
    return track_inputs