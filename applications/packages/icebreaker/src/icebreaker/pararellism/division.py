
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
    cluster_priority_percentages: dict,
    hardware_influence: float = 0.0
) -> any:
    try:
        import numpy as np
    except ImportError as e:
        raise ImportError("paralellism/division failed to import", e)
    '''
    Example
    resource-weights = {'CPU': 0.6,'RAM': 0.2,'GPU': 0.2}
    cluster_priorities = {'vm2': 0.60, 'lt3': 0.40, 'vm1': 0.0}
    '''
    clusters = {}
    # Normalize resource weights keys to uppercase for reliable matching
    normalized_resource_weights = {str(k).upper(): v for k, v in resource_weights.items()}
    resource_names = list(normalized_resource_weights.keys())

    for key, value in formatted_clusters.items():
        if 'clusters' in key:
            key_split = key.split('-')
            cluster_key = key_split[0] + '-' + key_split[2]
            pure_cluster_name = key_split[2] 
            
            if not cluster_key in clusters:
                clusters[cluster_key] = {'_pure_name': pure_cluster_name}

            if 'resources' in key:
                # Read the trailing segment and convert to uppercase to match resource configurations safely
                resource_type = key.split('-')[-1].upper()
                
                if resource_type in normalized_resource_weights:
                    if 'gpu' in key.lower():
                        if value == 'None':
                            clusters[cluster_key]['GPU'] = 0
                            clusters[cluster_key]['VRAM'] = 0
                            continue
                        clusters[cluster_key]['GPU'] = len(value)
                        for gpu_details in value:
                            gpu_vram = gpu_details['vram']
                            mib_val = 0
                            if 'MiB' in gpu_vram:
                                mib_val = int(gpu_vram.split(' ')[0])
                            if 'GB' in gpu_vram:
                                gb_amount = int(gpu_vram.split(' ')[0])
                                bytes_val = gb_amount * (10**9)
                                mib_val = bytes_val / (2**20)
                            clusters[cluster_key]['VRAM'] = round(mib_val)
                        continue
                    else:
                        if 'ram' in key.lower():
                            set_value = int(str(value).split(' ')[0])
                            clusters[cluster_key][resource_type] = set_value
                            continue
                        if 'nodes' in key.lower():
                            set_value = 0
                            if 'head' in str(value):
                                set_value += 1
                            if 'worker' in str(value):
                                worker_amount = int(str(value).split('-')[-1])
                                set_value += worker_amount
                            clusters[cluster_key][resource_type] = set_value
                            continue
                        else:
                            clusters[cluster_key][resource_type] = float(value)
    
    if not clusters:
        return {}
    
    if len(clusters) == 1:
        return {list(clusters.keys())[0]: 1.0}

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
    hardware_scores = normalized @ np.array(list(normalized_resource_weights.values()))
    
    # 2. Extract and Normalize User Priority Percentages
    priority_weights = []
    for cluster_key in clusters.keys():
        pure_name = clusters[cluster_key]['_pure_name']
        weight = cluster_priority_percentages.get(pure_name, 0.0)
        priority_weights.append(weight)
        
    priority_weights = np.array(priority_weights, dtype=float)
    if priority_weights.sum() > 0:
        priority_weights = priority_weights / priority_weights.sum()
    else:
        priority_weights = np.ones(len(clusters)) / len(clusters)

    # 3. Blend Scores
    final_scores = (hardware_influence * hardware_scores) + ((1.0 - hardware_influence) * priority_weights)
    
    total = final_scores.sum()
    if total == 0:
        final_weights = np.ones(len(clusters)) / len(clusters)
    else:
        final_weights = final_scores / total

    return dict(zip(clusters.keys(), final_weights))

def division_load_balanced_cluster_round_robin(
    target_list: any,
    cluster_weights: any,
    min_initial_inputs: int = 1,
    min_batch_size: int = 1
) -> any:
    try:
        import math
    except ImportError as e:
        raise ImportError("paralellism/division failed to import", e)

    clusters = list(cluster_weights.keys())
    if not clusters:
        return {} 

    assigned = {c: [] for c in clusters}
    # Sort items based on sizing constraint (smallest to biggest)
    weighted_items = sorted(target_list, key = lambda x: (x[-1]), reverse = False)
    total_items = len(weighted_items)
    
    if total_items == 0:
        return assigned

    # Sort clusters descending: Highest priority/percentage gets processed first
    sorted_clusters = sorted(clusters, key=lambda c: cluster_weights[c], reverse=True)

    # --- OVERSUBSCRIPTION GUARD CLAUSE ---
    required_initial_total = len(clusters) * min_initial_inputs
    if total_items < required_initial_total:
        item_idx = 0
        while item_idx < total_items:
            for c in sorted_clusters:
                if item_idx >= total_items:
                    break
                assigned[c].append(weighted_items[item_idx])
                item_idx += 1
        return assigned

    item_idx = 0

    # 1. GUARANTEED PASS: Distribute exactly M inputs to every cluster first
    for c in sorted_clusters:
        for _ in range(min_initial_inputs):
            assigned[c].append(weighted_items[item_idx])
            item_idx += 1

    # 2. PROPORTIONAL PASS: Calculate quotas for remaining items
    remaining_items_count = total_items - item_idx
    
    target_counts = {
        c: max(0, math.floor(cluster_weights[c] * remaining_items_count)) 
        for c in clusters
    }
    
    # Enforce minimum batch size rules for the remaining work allocation
    for c in clusters:
        if target_counts[c] > 0 and target_counts[c] < min_batch_size:
            target_counts[c] = min_batch_size

    # 3. Fill the buckets with the remaining items based on quotas
    for c in sorted_clusters:
        quota = target_counts[c]
        
        available_left = total_items - item_idx
        actual_quota = min(quota, available_left)
        
        if actual_quota <= 0:
            continue
            
        chunk = weighted_items[item_idx : item_idx + actual_quota]
        assigned[c].extend(chunk)
        item_idx += len(chunk)
        
    # 4. CLEAN-UP PASS: Handle any remaining fractional item leftovers
    while item_idx < total_items:
        highest_priority_cluster = sorted_clusters[0]
        assigned[highest_priority_cluster].append(weighted_items[item_idx])
        item_idx += 1

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