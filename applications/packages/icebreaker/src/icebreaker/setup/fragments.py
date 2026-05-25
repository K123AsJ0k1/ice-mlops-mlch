
def replace_yaml_fragments(
    base_dict: any,
    fragment_dicts: any,
    detail_dicts: any
) -> dict:
    try:
        import copy
    except ImportError as e:
        raise ImportError("Failed to import", e)
    
    if isinstance(base_dict, dict):
        for target_key, target_value in base_dict.items():
            if target_key in fragment_dicts:
                change_dict = {}
                if target_value == '{{value_fragment}}':
                    change_dict = copy.deepcopy(fragment_dicts[target_key])

                if target_value == '{{list_fragment}}':
                    change_dict = [copy.deepcopy(fragment_dicts[target_key])]
                # Consider putting the details in the fragments and then adding them into base dict
                if target_value == '{{dict_fragment}}':
                    for detail_dict in detail_dicts:
                        for details_key, details_values in detail_dict.items():
                            if target_key == details_key:
                                change_dict = copy.deepcopy(details_values)
                
                expanded_dict = replace_yaml_fragments(
                    base_dict = change_dict,
                    fragment_dicts = fragment_dicts,
                    detail_dicts = detail_dicts
                )

                base_dict[target_key] = expanded_dict
    return base_dict

def compose_yaml_dict(
    fragments_folder: str,
    fragments_prefix: str,
    root_fragment: str,
    details_folder: str,
    details_prefix: str,
    env_dict: dict,
    dict_inputs: any,
    output_folder: any,
    output_name: str
) -> dict:
    try:
        import os
        import yaml
        import re
        import copy
        from ..misc.dict import check_dict_path, update_dict_value, update_nested_dict
    except ImportError as e:
        raise ImportError("Failed to import", e)
    
    fragment_dicts = {}
    for root, dirs, files in os.walk(fragments_folder):
        for file in files:
            file_path = os.path.join(root, file)
            
            if fragments_prefix in file:
                print('Getting fragment: ' + str(file))
                content = None
                fragment_name = file.split('_')[0]
                with open(file_path, 'r') as f:
                    content = f.read()
                fragment_dicts[fragment_name] = yaml.safe_load(content)

    detail_dicts = []
    for root, dirs, files in os.walk(details_folder):
        for file in files:
            file_path = os.path.join(root, file)
            if details_prefix in file:
                print('Getting details: ' + str(file))
                content = None
                
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if 0 < len(env_dict):
                    pattern = r'\[([A-Z_1-9]+)\]'    
                    content = re.sub(
                        pattern,
                        lambda m: str(env_dict.get(m.group(1), m.group(0))),
                        content
                    )  
                    
                detail_dicts.append(yaml.safe_load(content))

    root_dict = fragment_dicts[root_fragment]
    pipeline_dict = replace_yaml_fragments(
        base_dict = root_dict,
        fragment_dicts = fragment_dicts,
        detail_dicts = detail_dicts
    )

    for detail_dict in detail_dicts:
        for details_key, details_values in detail_dict.items():
            if details_key in pipeline_dict:
                #print(details_key)
                #print(details_values)
                update_dict = {
                    details_key: details_values
                }
                print(update_dict)
                print('')
                modified_dict = update_nested_dict(
                    target_dict = pipeline_dict,
                    update_dict = update_dict
                )
                pipeline_dict = copy.deepcopy(modified_dict)

    for input_key, input_value in dict_inputs.items():
        path_exists = check_dict_path(
            target_dict = pipeline_dict,
            key_path = input_key,
            separator = '-'
        )
        print(input_key)
        if path_exists:
            update_dict_value(
                target_dict = pipeline_dict,
                key_path = input_key,
                separator = '-',
                new_value = input_value
            )
    
    if 0 < len(pipeline_dict):
        output_path = output_folder + '/' + output_name
        print('Creating output file: ' + str(output_path))
        with open(output_path, 'w') as f:
            yaml.safe_dump(
                pipeline_dict,
                f,
                indent = 2,
                default_flow_style = False,
                sort_keys = False
            )
    #pipeline_dict = {}
    return pipeline_dict 