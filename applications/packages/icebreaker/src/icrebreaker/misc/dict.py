
def check_dict_path(
    target_dict: any,
    key_path: any,
    separator: str
) -> bool:
    keys = key_path.split(separator)
    current_level = target_dict
    for key in keys:
        if isinstance(target_dict, dict) and key in current_level:
            current_level = current_level[key]
        else:
            return False
    return True

def get_dict_value(
    target_dict: any,
    key_path: any,
    separator: str
) -> any: 
    keys = key_path.split(separator)
    current_level = target_dict
    for key in keys[:-1]:
        current_level = current_level[key]
    last_key = keys[-1]
    return current_level[last_key]

def update_dict_value(
    target_dict: any,
    key_path: any,
    separator: str,
    new_value: any
):
    keys = key_path.split(separator)
    current_level = target_dict
    for key in keys[:-1]:
        current_level = current_level[key]
    last_key = keys[-1]
    current_level[last_key] = new_value

def create_nested_dict(
    target_dict: any,
    key_path: any,
    separator: str
):
    keys = key_path.split(separator)
    current_level = target_dict
    for key in keys:
        current_level = current_level.setdefault(key, {})
    return target_dict

def fill_nested_dict(
    target_dict: any,
    source_dict: any
) -> dict:
    try:
        from collections.abc import Mapping
    except ImportError as e:
        raise ImportError("Failed to import", e)

    for key, value in source_dict.items():
        if isinstance(value, Mapping) and key in target_dict and isinstance(target_dict[key], Mapping):
            fill_nested_dict(target_dict[key], value)
        else:
            target_dict[key] = value
    return target_dict

def create_flat_dict(
    target_dict: any,
    parent_key: str,
    separator: str
) -> any:
    items = []
    for k, v in target_dict.items():
        new_key = parent_key + separator + k if parent_key else k
    
        if isinstance(v, dict) and v:
            items.extend(create_flat_dict(v, new_key, separator).items())
        else:
            items.append((new_key, v))
    return dict(items)

def update_nested_dict(
    target_dict: any, 
    update_dict: any
) -> any:
    # Be aware that this is vunerable to aliasing problem
    # which you might need to fix with deepcopy
    # Example is giving different keys the same dict
    # which means without deepcopy you will modify the same
    # memory addressses
    for key, value in update_dict.items():
        if isinstance(value, dict):
            target_dict[key] = update_nested_dict(target_dict.get(key, {}), value)
        elif isinstance(value, list):
            target_value = target_dict.get(key)
            update_list_value = value[0]
            #print('General list')
            #print(key, value)
            if isinstance(target_value, list):
                target_list_value = target_value[0]
                if isinstance(update_list_value, dict) and isinstance(target_list_value, dict):
                    #print('List dict')
                    updated_list = []
                    index = 0
                    for i in range(0, len(value)):
                        value_list_dict = value[index]
                        if index < len(target_value):
                            target_list_dict = target_value[index]
                            updated_list.append(update_nested_dict(target_list_dict, value_list_dict))
                        else:
                            updated_list.append(value_list_dict)
                        index += 1
                    target_dict[key] = updated_list

                if not isinstance(update_list_value, dict) or not isinstance(target_list_value, dict):
                    target_dict[key] = value
            else:
                target_dict[key] = value
        else:
            # This will fail for updates that want 
            # to add a dict as the last value
            # Example is target {'languages': 'fill'} and update {'languages': {'python': 'fill'}}
            # The solution is to just declare python in the target for update
            target_dict[key] = value
    return target_dict

def flatten_nested_dict(
    target_dict: any,
    parent_key: str,
    seperator: str
): 
    items = []
    for k, v in target_dict.items():
        new_key = f"{parent_key}{seperator}{k}" if parent_key else k
        if isinstance(v, dict):
            # Recursively flatten if the value is another dictionary
            items.extend(flatten_nested_dict(v, new_key, seperator).items())
        else:
            items.append((new_key, v))
    return dict(items)

def split_dict_by_length(
    dict_lists: dict, 
    list_length: int
):
    max_len = max(len(v) for v in dict_lists.values())
    
    num_chunks = math.ceil(max_len / list_length)
    
    for i in range(num_chunks):
        start = i * list_length
        end = start + list_length
        yield {k: v[start:end] for k, v in dict_lists.items() if v[start:end]}