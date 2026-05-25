
def replace_yaml_fragments(
    base_dict: any,
    fragment_dicts: any,
    detail_dicts: any
) -> dict:
    try:
        import copy
    except ImportError as e:
        raise ImportError("Setup/fragments failed to import", e)
    
    # '{{value_fragment}}' = fragment that contains only key-value pairs, not nested dictionaries
    # '{{list_fragment}}' = fragment that contains lists of dicts that can be nested dictioanries
    # '{{dict_fragment}}' = fragment that contains dictionaries that are nested dictionaries
    # 'fill' = default string value meant to be filled later 
    # {} = default dict value meant to be filled later
    # 0 = default number value meant to be filled later

    def resolve(template_val, details_list, key_name=None):
        if not isinstance(details_list, list):
            details_list = [details_list]

        # 1. Global Fragment Template Inheritance
        if key_name in fragment_dicts:
            fragment_base = copy.deepcopy(fragment_dicts[key_name])
            if template_val == '{{list_fragment}}':
                base_structure = [fragment_base]
            else:
                base_structure = fragment_base
            
            combined_details = []
            combined_details.extend(details_list)
            if template_val not in ['{{dict_fragment}}', '{{value_fragment}}', '{{list_fragment}}']:
                combined_details.append(template_val)
            for g_dict in detail_dicts:
                if isinstance(g_dict, dict) and key_name in g_dict:
                    combined_details.append(g_dict[key_name])
            
            return resolve(base_structure, combined_details, key_name=None)

        # 2. Handle Fragment Placeholders without matching template files
        if isinstance(template_val, str) and template_val in ['{{dict_fragment}}', '{{value_fragment}}', '{{list_fragment}}']:
            if details_list:
                return resolve(details_list[0], details_list)
            else:
                return template_val

        # 3. Context-Aware Deep Dictionary Merging
        if isinstance(template_val, dict):
            result = {}
            all_keys = list(template_val.keys())
            for d in details_list:
                if isinstance(d, dict):
                    for k in d.keys():
                        if k not in all_keys:
                            all_keys.append(k)
            
            for k in all_keys:
                sub_details = []
                for d in details_list:
                    if isinstance(d, dict) and k in d:
                        sub_details.append(d[k])
                
                if k in template_val:
                    result[k] = resolve(template_val[k], sub_details, key_name=k)
                else:
                    if sub_details:
                        result[k] = resolve(sub_details[0], sub_details, key_name=k)
            return result

        # 4. List Structural Parsing
        elif isinstance(template_val, list):
            sub_details_flat = []
            for d in details_list:
                if isinstance(d, list):
                    sub_details_flat.extend(d)
                else:
                    sub_details_flat.append(d)
            return [resolve(item, sub_details_flat) for item in template_val]

        # 5. Fixed Scalar Substitution (Prevents Infinite Loops)
        else:
            for d in details_list:
                if d is not None and d != 'fill' and not (isinstance(d, str) and d in ['{{dict_fragment}}', '{{value_fragment}}', '{{list_fragment}}']):
                    # ONLY recurse if the replacement layer is a structural object (dict/list)
                    if isinstance(d, (dict, list)):
                        return resolve(d, details_list)
                    # If it's a primitive type (str, int, bool), return it directly!
                    return d
            return template_val

    return resolve(base_dict, detail_dicts)

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
        from ..misc.dict import check_dict_path, update_dict_value
    except ImportError as e:
        raise ImportError("Setup/fragments failed to import", e)
    
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
    
    for input_key, input_value in dict_inputs.items():
        path_exists = check_dict_path(
            target_dict = pipeline_dict,
            key_path = input_key,
            separator = '|'
        )
        if path_exists:
            update_dict_value(
                target_dict = pipeline_dict,
                key_path = input_key,
                separator = '|',
                new_value = input_value
            )
    
    if 0 < len(pipeline_dict):
        if 0 < len(output_folder):
            for root, dirs, files in os.walk(output_folder):
                print('Checking folder')
                file_version = 1
                for file in files:
                    if output_name in file:
                        file_version += 1
                
                file_name = output_name + '_' + str(file_version) + '.yaml'
                output_path = os.path.join(root, file_name)
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