
def replace_yaml_fragments(
    base_dict: any,
    fragment_dicts: any,
    details_dicts: any
) -> dict:
    try:
        import copy
        from misc.dict import update_nested_dict
    except ImportError as e:
        raise ImportError("Failed to import", e)

    if isinstance(base_dict, dict):
        for target_key, target_value in base_dict.items():
            if target_key in fragment_dicts:
                change_dict = {}
                if target_value == '{{dict_fragment}}' or target_value == '{{value_fragment}}':
                    change_dict = copy.deepcopy(fragment_dicts[target_key])
                if target_value == '{{list_fragment}}':
                    change_dict = [copy.deepcopy(fragment_dicts[target_key])]
                
                expanded_dict = replace_yaml_fragments(
                    base_dict = change_dict,
                    fragment_dicts = fragment_dicts,
                    details_dicts = details_dicts
                )
                
                if target_value == '{{dict_fragment}}':
                    dict_fragment = {}
                    for details_key, details_values in details_dicts.items():
                        details_split = details_key.split('_')
                        details_root = details_split[0]
                        details_name = details_split[1]
                        if target_key ==  details_root:
                            # This does not add missing time fragments
                            modified_dict = update_nested_dict(
                                target_dict = expanded_dict, 
                                update_dict = details_values
                            )
                            dict_fragment[details_name] = copy.deepcopy(modified_dict)
                    expanded_dict = dict_fragment
                base_dict[target_key] = expanded_dict
    return base_dict

def compose_yaml_dict(
    fragments_folder: str,
    fragments_prefix: str,
    fragments_order: list,
    details_folder: str,
    details_prefix: str,
    details_order: list,
    env_dict: dict,
    dict_inputs: any,
    output_folder: any,
    output_name: str
) -> dict:
    try:
        import yaml
        import re
        from misc.dict import check_dict_path, update_dict_value
    except ImportError as e:
        raise ImportError("Failed to import", e)

    # Check if there is a need to timestamp
    fragment_dicts = {}
    for name in fragments_order:
        fragment_path = fragments_folder + '/' + name + fragments_prefix
        print('Getting fragment: ' + str(name))
        content = None
        with open(fragment_path, 'r') as f:
            content = f.read()
        fragment_dicts[name] = yaml.safe_load(content)

    detail_dicts = {}
    for name in details_order:
        details_path = details_folder + '/' + name + details_prefix
        print('Getting details: ' + str(details_path))
        content = None
        with open(details_path, 'r') as f:
            content = f.read()
        pattern = r'\[([A-Z_1-9]+)\]'    
        updated_content = re.sub(
            pattern,
            lambda m: str(env_dict.get(m.group(1), m.group(0))),
            content
        )  
        detail_dicts[name] = yaml.safe_load(updated_content)
    
    root_dict = fragment_dicts[fragments_order[0]]
    pipeline_dict = replace_yaml_fragments(
        base_dict = root_dict,
        fragment_dicts = fragment_dicts,
        details_dicts = detail_dicts
    )

    for input_key, input_value in dict_inputs.items():
        path_exists = check_dict_path(
            target_dict = pipeline_dict,
            key_path = input_key,
            separator = '-'
        )
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
    return pipeline_dict 