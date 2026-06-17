
def division_data_round_robin(
    target_list: any, 
    number: int
) -> any:
    lists = [[] for _ in range(number)]
    i = 0
    for elem in target_list:
        lists[i].append(elem)
        i = (i + 1) % number
    return lists

def division_formatted_clusters(
    ray_clusters: any
) -> any: 
    try:
        import copy
        import numpy as np
        from ..misc.dict import flatten_nested_dict
    except ImportError as e:
        raise ImportError("Failed to import", e)

    available_clusters = copy.deepcopy(ray_clusters)
    # nodes, CPU, RAM, GPU, VRAM
    collective = [0,0,0,0,0]
    flattened_dict = flatten_nested_dict(
        target_dict = available_clusters,
        parent_key = '',
        seperator = '-'
    )
    
    for key, value in flattened_dict.items():
        if 'nodes' in key:
            if 'head' in value:
                collective[0] += 1
            if 'worker' in value:
                worker_amount = int(value.split('-')[-1])
                collective[0] += worker_amount
        if 'cpu' in key:
            collective[1] += int(value) 
        if 'ram' in key:
            gb_val = int(value.split(' ')[0])
            collective[2] += gb_val
        if 'gpu' in key:
            if not value == 'None':
                collective[3] += len(value)
                for gpu_details in value:
                    gpu_vram = gpu_details['vram']
                    mib_val = 0
                    if 'MiB' in gpu_vram:
                        mib_val = int(gpu_vram.split(' ')[0])
                    if 'GB' in gpu_vram:
                        gb_amount = int(gpu_vram.split(' ')[0])
                        bytes_val = gb_amount * (10**9)
                        mib_val = bytes_val / (2**20)
                    collective[4] += mib_val

    flattened_dict['collective-nodes'] = collective[0]
    flattened_dict['collective-cpu'] = collective[1]
    flattened_dict['collective-ram'] = collective[2]
    flattened_dict['collective-gpu'] = collective[3]
    flattened_dict['collective-vram'] = collective[4]
                    
    return flattened_dict

def division_cluster_weights(
    resource_weights: any,
    formatted_clusters: any,
    cluster_priorities: dict
) -> any:
    try:
        import numpy as np
    except ImportError as e:
        raise ImportError("Failed to import", e)
    '''
    Example
    'resource-weights': {'CPU': 0.6,'RAM': 0.2,'GPU': 0.2}
    cluster_priorities = ['vm2', 'lt3', 'lt2', 'vm1', 'lt1']
    '''
    clusters = {}
    for key, value in formatted_clusters.items():
        if 'clusters' in key:
            key_split = key.split('-')
            cluster_key = key_split[0] + '-' + key_split[2]
            
            pure_cluster_name = key_split[2] 
            if not cluster_key in clusters:
                clusters[cluster_key] = {'_pure_name': pure_cluster_name}

            if 'resources' in key:
                resource_type = key.split('-')[-1]
                if resource_type in resource_weights:
                    if 'gpu' in key:
                        if value == 'None':
                            clusters[cluster_key]['gpu'] = 0
                            clusters[cluster_key]['vram'] = 0
                            continue
                        clusters[cluster_key]['gpu'] = len(value)
                        for gpu_details in value:
                            gpu_vram = gpu_details['vram']
                            mib_val = 0
                            if 'MiB' in gpu_vram:
                                mib_val = int(gpu_vram.split(' ')[0])
                            if 'GB' in gpu_vram:
                                gb_amount = int(gpu_vram.split(' ')[0])
                                bytes_val = gb_amount * (10**9)
                                mib_val = bytes_val / (2**20)
                            clusters[cluster_key]['vram'] = round(mib_val)
                        continue
                    else:
                        if 'ram' in key:
                            set_value = int(value.split(' ')[0])
                            clusters[cluster_key][resource_type] = set_value
                            continue
                        if 'nodes' in key:
                            set_value = 0
                            if 'head' in value:
                                set_value += 1
                            if 'worker' in value:
                                worker_amount = int(value.split('-')[-1])
                                set_value += worker_amount
                            clusters[cluster_key][resource_type] = set_value
                            continue
                        else:
                            clusters[cluster_key][resource_type] = value
    
    if not clusters:
        return {}
    
    if len(clusters) == 1:
        return {list(clusters.keys())[0]: 1.0}

    resource_names = list(resource_weights.keys())
    for c in clusters:
        for r in resource_names:
            if r not in clusters[c]:
                clusters[c][r] = 0.0

    resource_matrix = np.array([
        [clusters[c][r] for r in resource_names]
        for c in clusters
    ], dtype=float)

    max_values = resource_matrix.max(axis=0)

    max_values[max_values == 0] = 1.0 

    normalized = resource_matrix / max_values
    weighted_scores = normalized @ np.array(list(resource_weights.values()))
    total = weighted_scores.sum()
    
    if 0 < len(cluster_priorities):
        # Create a mapping of priority tiers. 
        # Example: if 5 clusters, highest priority gets 5x multiplier, lowest gets 1x multiplier.
        cluster_names = cluster_priorities.keys()
        total_priorities = len(cluster_names)
        priority_map = {name: (total_priorities - idx) for idx, name in enumerate(cluster_names)}
        
        # Apply the multiplier to each cluster's resource score
        for idx, cluster_key in enumerate(clusters.keys()):
            pure_name = clusters[cluster_key]['_pure_name']
            # Fallback to 1 if a cluster isn't explicitly listed in priorities
            multiplier = priority_map.get(pure_name, 1)  
            weighted_scores[idx] *= multiplier

    final_weights = []
    if total == 0:
        # If all clusters scored 0, distribute work equally
        final_weights = np.ones(len(clusters)) / len(clusters)
    else:
        final_weights = weighted_scores / total

    return dict(zip(clusters.keys(), final_weights))

def division_load_balanced_cluster_round_robin(
    target_list: any,
    cluster_weights: any
) -> any:
    clusters = list(cluster_weights.keys())

    if not clusters:
        return {} 

    assigned = {c: [] for c in clusters}
    cluster_load = {c: 0 for c in clusters}
    # This sorts based on the last tuple value
    # that is in this case size from smallest to biggest
    weighted_items = sorted(target_list, key = lambda x: (x[-1]), reverse = False)
    capacities = {c: cluster_weights[c] for c in clusters}
    for item_tuple in weighted_items:
        target = min(
            clusters,
            key=lambda c: cluster_load[c] / capacities[c] if capacities[c] > 0 else float('inf')
        )
        
        # Guard clause: If ALL available clusters have 0 capacity, 
        # float('inf') will tie. Python's min() defaults to the first one.

        assigned[target].append(item_tuple)
        cluster_load[target] += item_tuple[-1]
    return assigned

def division_split_input(
    job_input: list, 
    num_workers: int
) -> any:
    try:
        import math
    except ImportError as e:
        raise ImportError("pararellism/division failed to import", e)

    if num_workers <= 0:
        raise ValueError("Number of workers must be greater than 0.")
        
    # Handle edge case where you have more workers than actual files
    if num_workers > len(job_input):
        num_workers = len(job_input)
        
    # Determine the standard size of each batch
    batch_size = math.ceil(len(job_input) / num_workers)
    
    # Slice the original list into sub-lists
    return [job_input[i : i + batch_size] for i in range(0, len(job_input), batch_size)]