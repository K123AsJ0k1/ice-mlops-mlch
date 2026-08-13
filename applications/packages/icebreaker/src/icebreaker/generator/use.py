
def generate_create_requests(
    swift_client: any,
    storage_parameters: any,
    dataset_paths: list,
    prompt_parameters: any,
    data_ratio: any,
    join_prompts: bool
):
    try:
        from ..objects.use import objects_get_data
        import re
        import json
    except ImportError as e:
        raise ImportError("generator/ failed to import", e)

    print('Creating inference requests')
    inference_requests = []
    case_idx = 0
    question_type_idx = {}
    valid_data_rows = {}
    for dataset_path in dataset_paths:
        data_object = objects_get_data(
            swift_client = swift_client,
            storage_parameters = {
                'bucket-target': storage_parameters['bucket-target'],
                'bucket-prefix': storage_parameters['bucket-prefix'],
                'bucket-user': storage_parameters['bucket-user'],
                'object-name': 'root',
                'object-serialization': storage_parameters['object-serialization'],
                'path-replacers': {
                    'name': dataset_path
                },
                'path-names': [],
                'debug-prints': True,
                'lock-parameters': {},
                'lock-location': None,
                'overwrite': True
            },
            dict_format = False
        )    
        dataset_name = dataset_path.split('/')[-1].split('.')[0]
        valid_data_rows[dataset_name] = 0

        target_df = data_object[0]

        for _, row in target_df.iterrows():
            if row['chapter'] == 0:
                continue
            valid_data_rows[dataset_name] += 1  
            row_chapter = row['chapter']
            row_idx = row['idx']
            row_char = row['characters']
            replacer_dict = {
                'CONTENT': row['content'],
                'MATERIAL': json.dumps(row['ref-material'], indent=2),
                'PATHS': json.dumps(row['ref-paths'], indent=2)
            }
            for data_type, wanted_amount in data_ratio.items():
                if not data_type in question_type_idx:
                    question_type_idx[data_type] = 0
                
                system_prompt = prompt_parameters[data_type]['system-prompt']
                user_template = prompt_parameters[data_type]['user-template']
                temperature = prompt_parameters[data_type]['temperature']
                top_p = prompt_parameters[data_type]['top-p']
                max_tokens = prompt_parameters[data_type]['max-tokens']

                pattern = r'\[([A-Z_1-9]+)\]'
                user_prompt = re.sub(
                    pattern, 
                    lambda m: str(replacer_dict.get(m.group(1), m.group(0))), 
                    user_template
                )
                sent_messages = []
                system_prompt_length = 0
                user_prompt_length = 0
                if join_prompts:
                    joined_prompt = f'{system_prompt}\n{user_prompt}'
                    user_prompt_length = len(joined_prompt)
                    sent_messages.append({
                        "role": "user", 
                        "content": joined_prompt
                    })
                else:
                    system_prompt_length = len(system_prompt)
                    sent_messages.append({
                        "role": "system", 
                        "content": system_prompt
                    })
                    user_prompt_length = len(user_prompt)
                    sent_messages.append({
                        "role": "user", 
                        "content": user_prompt
                    })

                for i in range(0, wanted_amount):
                    inference_requests.append({
                        'dataset-name': dataset_name,
                        'row-chapter': row_chapter,
                        'row-index': row_idx,
                        'row-characters': row_char,
                        'case-index': case_idx,
                        'question-type': data_type,
                        'question-index': question_type_idx[data_type],
                        'messages': sent_messages,
                        'system-prompt-length': system_prompt_length,
                        'user-prompt-length': user_prompt_length,
                        'temperature': temperature,
                        'top-p': top_p,
                        'max-tokens': max_tokens
                    })
                    question_type_idx[data_type] += 1
            case_idx += 1
    print('')
    print('Valid cases per dataset')
    for key, value in valid_data_rows.items():
        print(f'{key}|{value}')
    print(f'Amount of requests: {len(inference_requests)}')
    return inference_requests

def generate_create_outputs(
    dataset_inference_requests: list,
    request_keys: dict,
    length_limit: int,
    inference_parameters: any,
    debug_prints: bool
) -> dict:
    try:
        from ..ray.use import ray_serve_route
        import statistics
        import time as t
    except ImportError as e:
        raise ImportError("generator/ failed to import", e)
    process_time_start = t.time()
    print('Creating dataset')
    print(f'Request length limit {length_limit}')
    print('')
    inference_address = inference_parameters['address']
    inference_path = inference_parameters['path']
    prompt_lengths = []
    dataset_metadata = []
    model_outputs = []
    gathered_metrics = []
    request_times = []
    # The end dataset also required input for double checking
    # There should be columns for messages
    for inference_requests in dataset_inference_requests:
        sent_request = {}
        dataset_name = inference_requests['dataset-name']
        row_chapter = inference_requests['row-chapter']
        row_index = inference_requests['row-index']
        row_characters = inference_requests['row-characters']
        case_index = inference_requests['case-index'] + 1
        question_type = inference_requests['question-type']
        question_index = inference_requests['question-index'] + 1
        system_prompt_length = inference_requests['system-prompt-length']
        user_prompt_length = inference_requests['user-prompt-length']
        temperature = inference_requests['temperature']
        top_p = inference_requests['top-p']
        max_tokens = inference_requests['max-tokens']

        if user_prompt_length < length_limit:
            if 0 < system_prompt_length:
                prompt_lengths.append(system_prompt_length)
            if 0 < user_prompt_length:
                prompt_lengths.append(user_prompt_length)

            print(f'Dataset|{dataset_name}')
            print(f'Chapter|{row_chapter}')
            print(f'Index|{row_index}')
            print(f'Characters|{row_characters}')
            print(f'Case|{case_index}')
            print(f'Question type|{question_type}')
            print(f'Question index|{question_index}')
            print(f'System prompt length|{system_prompt_length}')
            print(f'User prompt length|{user_prompt_length}')
            print(f'Temperature|{temperature}')
            print(f'Top-p|{top_p}')
            print(f'Max tokens|{max_tokens}') 

            for key in request_keys:
                sent_request[key] = inference_requests[key]

            request_time_start = t.time()
            print('Sending request')
            status_code, route_output = ray_serve_route(
                route_address = inference_address,
                route_path = inference_path,
                route_type = 'POST',
                route_input = sent_request,
                timeout = 5
            )

            request_end_time = t.time()
            request_total_time = round(request_end_time-request_time_start,5)
            print(f'Spent seconds request: {request_total_time}')

            if status_code == 200:
                print('Request success')
                output_status = route_output['status']

                if output_status == 'success':
                    generated_data = route_output['text']
                    effiency_metrics = route_output['efficiency-metrics']
                    dataset_metadata.append({
                        'dataset': dataset_name,
                        'case-chapter': row_chapter,
                        'row-index': row_index,
                        'characters': row_characters,
                        'case-index': case_index,
                        'question-type': question_type,
                        'question-index': question_index,
                        'system-prompt-length': system_prompt_length,
                        'user-prompt-length': user_prompt_length,
                        'temperature': temperature,
                        'max-tokens': max_tokens
                    })
                    model_outputs.append(generated_data)
                    gathered_metrics.append(effiency_metrics)
                    request_times.append(request_total_time)
            else:
                print('Request fail')
        print('')

    length_mean = statistics.mean(prompt_lengths)
    length_median = statistics.median(prompt_lengths)
    max_prompt_length = max(prompt_lengths)
    min_prompt_length = min(prompt_lengths)

    print(f'Max prompt length|{max_prompt_length}')
    print(f'Min prompt length|{min_prompt_length}')
    print(f'Mean prompt length|{length_mean}')
    print(f'Median prompt length|{length_median}')
    
    process_end_time = t.time()
    process_total_time = round(process_end_time-process_time_start,5)
    print(f'Spent seconds on processing: {process_total_time}')

    general_stats = {
        'length-mean': length_mean,
        'length-median': length_median,
        'max-prompt-length': max_prompt_length,
        'min-prompt-length': min_prompt_length,
        'process-total-time': process_total_time
    }
    
    return model_outputs, gathered_metrics, request_times, general_stats

def generate_parse_output(
    text: str
) -> any:
    try:
        import re
    except ImportError as e:
        raise ImportError("generator/use failed to import", e)
    
    if '</think>' in text:
        parts = text.split('</think>', 1)
        thinking_text = parts[0].strip()
        main_content = parts[1].strip()
    else:
        thinking_text = ""
        main_content = text

    sections = re.split(r'\n(?=###\s+)', main_content)

    parsed_sections = {}
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        
        # Match '### HEADER_NAME\n Header Content'
        header_match = re.match(r'^###\s+([^\n]+)\n?(.*)', sec, flags=re.DOTALL)
        if header_match:
            header_title = header_match.group(1).strip().lower().replace("_", "-")
            header_content = header_match.group(2).strip()
            parsed_sections[header_title] = header_content

    return {
        'thinking-text': thinking_text,
        'main-content': main_content,
        **parsed_sections
    }

def generate_process_references(
    used_references: str,
) -> any:
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("generator/use failed to import", e)

    # N/A
    if 'N/A' in used_references:
        return pd.NA

    # There can be many
    # #used-material-n or n
    if not '(' in used_references or not ')' in used_references:
        # #used-material-n
        if '#used-material' in used_references:
            return used_references

    if '(' in used_references or ')' in used_references:
        return used_references.replace("(", "").replace(")", "")

    return 'Hallucinated'
    
def generate_process_paths(
    used_paths: str
) -> any:
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("generator/use failed to import", e)
    #print('paths')
    #print(used_paths)
    if 'N/A' in used_paths:
        return pd.NA

    if not '(' in used_paths or not ')' in used_paths:
        # #used-material-n
        #print(used_paths)
        if './docs/config/settings.yaml' in used_paths:
            return pd.NA

        if './' in used_paths:
            return used_paths
    
    if '(' in used_paths or ')' in used_paths:
        if './docs/config/settings.yaml' in used_paths:
            return pd.NA

        return used_paths.replace("(", "").replace(")", "")

    return 'Hallucinated'

def generate_process_category(
    answer: str
) -> any:
    try:
        import pandas as pd
        import re
    except ImportError as e:
        raise ImportError("generator/use failed to import", e)

    pattern = r'^\[(?P<action>[^-\]]+)(?:\s*-\s*(?P<type>[^\]]+))?\]\s*:\s*(?P<ground_truth>.*)$'
    match = re.match(pattern, answer.strip(), flags=re.DOTALL)
    
    if match:
        return {
            'action': match.group('action').strip(),
            'category': match.group('type').strip() if match.group('type') else None,
            'ground-truth-answer': match.group('ground_truth').strip()
        }
    
    # Fallback if the pattern doesn't match bracketed prefix
    return {
        'action': pd.NA,
        'category': pd.NA,
        'ground-truth-answer': answer.strip()
    }
    
def generate_process_data(
    inference_requests: list,
    model_outputs: list,
    gathered_metrics: list,
    request_times: list
):
    try:
        import pandas as pd
        from ..generator.use import generate_parse_output
    except ImportError as e:
        raise ImportError("generator/use failed to import", e)

    expanded_df = pd.json_normalize(inference_requests)
    dataset_df_temp = pd.DataFrame(gathered_metrics)
    dataset_df_temp['times'] = request_times
    
    temp_2_df = pd.concat([expanded_df, dataset_df_temp], axis = 1)
    output_list = []
    for output in model_outputs:
        output_dict = generate_parse_output(
            text = output
        )
        
        if 'type' in output_dict:
            if output_dict['type'] == 'factual' or output_dict['type'] == 'synthesis':
                if 'relevant-used-references' in output_dict and 'relevant-used-paths' in output_dict:
                    checked_references = generate_process_references(
                        used_references = output_dict['relevant-used-references']
                    )
                    output_dict['relevant-used-references'] = checked_references
                    checked_paths = generate_process_paths(
                        used_paths = output_dict['relevant-used-paths']
                    )
                    output_dict['relevant-used-paths'] = checked_paths

            if output_dict['type'] == 'negative':
                if 'ground-truth-answer' in output_dict:
                    category_data = generate_process_category(
                        answer = output_dict['ground-truth-answer']
                    )
                    
                    for key, value in category_data.items():
                        output_dict[key] = value

        output_list.append(output_dict)
        
    output_df = pd.json_normalize(output_list)
    preprocess_df = pd.concat([temp_2_df, output_df], axis = 1)
    preprocess_df = preprocess_df.loc[:, ~preprocess_df.columns.duplicated()]
    preprocess_df = preprocess_df.convert_dtypes()

    return preprocess_df
    
   