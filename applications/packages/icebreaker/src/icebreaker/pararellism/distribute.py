def distribute_step_inputs(
    storage_client: any,
    integration: dict,
    processing: dict
):
    try:
        from ..ray.use import ray_get_clients
        from ..objects.use import objects_get_prefix_list, objects_get_data
        from ..pararellism.division import (
            division_formatted_clusters, 
            division_cluster_weights,
            division_load_balanced_cluster_round_robin,
            division_load_balanced_cluster_dataframe_ranges
        )
    except ImportError as e:
        raise ImportError("pararellism/distribute to import", e)
    
    cluster_yamls = integration['cluster-yamls']
    cluster_priority = integration['cluster-priority']
    hardware_influence = integration['hardware-influence']
    workflow_steps = integration['workflow-steps']
    resource_weights = integration['resource-weights']
    min_initial_inputs = integration['min-initial-inputs']
    min_batch_size = integration['min-batch-size']
     
    cluster_tracks = {}
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
            # This will fail if there is changes in step general details
            # This needs to be changed to allow table index range divsion

            input_storage = processing[step_key]['general']['input-storage']            
            if 'path-prefix' in input_storage:
                path_prefix = input_storage['path-prefix']
                print(f'Used path prefix:{path_prefix}')
                dataset_tuple_list = objects_get_prefix_list(
                    storage_client = storage_client,
                    storage_parameters = input_storage,
                    path_prefix = path_prefix
                ) 

                cluster_division = division_load_balanced_cluster_round_robin(
                    target_list = dataset_tuple_list,
                    cluster_weights = cluster_weights,
                    min_initial_inputs = min_initial_inputs,
                    min_batch_size = min_batch_size
                )

            if 'object-path' in input_storage:
                object_path = input_storage['object-path']
                print(f'Used object path: {object_path}')

                input_storage['object-name'] = 'root'
                input_storage['path-replacers'] = {
                    'name': object_path
                }
                input_storage['path-names'] = []
                input_storage['debug-prints'] = True
                input_storage['lock-parameters'] = {}
                input_storage['lock-location'] = None
                input_storage['overwrite'] = True

                target_object = objects_get_data(
                    swift_client = storage_client,
                    storage_parameters = input_storage,
                    dict_format = False
                )
                target_dataset = target_object[0]

                cluster_division = division_load_balanced_cluster_dataframe_ranges(
                    cluster_weights = cluster_weights,
                    total_rows = len(target_dataset),
                    min_batch_size = min_batch_size
                )
            
            for cluster_name, cluster_input in cluster_division.items():
                print(f'{cluster_name} given batch input size {str(len(cluster_input))}')
                if not cluster_name in cluster_tracks:
                    cluster_tracks[cluster_name] = []
                
                cluster_tracks[cluster_name].append({
                    'cluster_step': step_key,
                    'cluster_name': cluster_name,
                    'cluster_input': cluster_input
                })
    track_inputs = []
    for used_name, used_input in cluster_tracks.items():
        track_inputs.append(used_input)
    return track_inputs