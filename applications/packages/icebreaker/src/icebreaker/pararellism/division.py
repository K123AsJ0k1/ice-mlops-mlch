
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
    cluster_priorities: list,
    temperature: float
) -> any:
    try:
        import numpy as np
    except ImportError as e:
        raise ImportError("paralellism/division failed to import", e)
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
        total_priorities = len(cluster_priorities)
        
        # 1. Create a clean, linear rank step (e.g., 5, 4, 3, 2, 1)
        priority_ranks = []
        for cluster_key in clusters.keys():
            pure_name = clusters[cluster_key]['_pure_name']
            # Find its rank index. If not found, place it at the bottom
            try:
                rank = total_priorities - cluster_priorities.index(pure_name)
            except ValueError:
                rank = 1
            priority_ranks.append(rank)
            
        priority_ranks = np.array(priority_ranks, dtype=float)
        
        # 2. Apply Softmax with a Temperature setting to enforce a radical skew
        # Lower temperature = much more radical distribution favoring top priorities
        exp_ranks = np.exp(priority_ranks / temperature)
        priority_weights = exp_ranks / np.sum(exp_ranks)
        
        # 3. Combine the hardware capacity with the new radical priority weights
        weighted_scores = weighted_scores * priority_weights

    final_weights = []
    if total == 0:
        # If all clusters scored 0, distribute work equally
        final_weights = np.ones(len(clusters)) / len(clusters)
    else:
        final_weights = weighted_scores / total

    return dict(zip(clusters.keys(), final_weights))

def division_load_balanced_cluster_round_robin(
    target_list: any,
    cluster_weights: any,
    min_batch_size: int
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

    # 1. Calculate ideal exact target capacities based strictly on the weights
    # Example: weight 0.40 * 126 items = 50 items targeted for this cluster
    target_counts = {c: max(0, math.floor(cluster_weights[c] * total_items)) for c in clusters}
    
    # Enforce minimum batch size rules for clusters that qualify for work
    for c in clusters:
        if target_counts[c] > 0 and target_counts[c] < min_batch_size:
            target_counts[c] = min_batch_size

    # 2. Sort clusters by weight descending so high-priority clusters pick their items first
    sorted_clusters = sorted(clusters, key=lambda c: cluster_weights[c], reverse=True)
    
    item_idx = 0
    
    # 3. Primary allocation pass: Fill high priority buckets up to their mathematical quota
    for c in sorted_clusters:
        quota = target_counts[c]
        # Allocate a continuous chunk of items to this cluster
        chunk = weighted_items[item_idx : item_idx + quota]
        assigned[c].extend(chunk)
        item_idx += len(chunk)
        
    # 4. Clean-up pass: If any remaining fractional items exist due to rounding, 
    # give them strictly to the highest-weight cluster that has capacity
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