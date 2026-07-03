
def generate_create_dataset(
    swift_client: any,
    storage_parameters: any,
    dataset_paths: list,
    prompt_parameters: any,
    data_ratio: any,
    join_prompts: bool,
    request_keys: dict,
    length_limit: int,
    inference_parameters: any,
    debug_prints: bool
) -> dict:
    try:
        from ..objects.use import objects_get_data
        from ..ray.use import ray_serve_route
        import re
        import json
        import statistics
        import time as t
    except ImportError as e:
        raise ImportError("generator/ failed to import", e)
    
    process_time_start = t.time()

    dataset_inference_requests = []
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
                    dataset_inference_requests.append({
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
                        'max-tokens': max_tokens,
                    })
                    question_type_idx[data_type] += 1
            case_idx += 1
    print('')
    print('Valid cases per dataset')
    for key, value in valid_data_rows.items():
        print(f'{key}|{value}')
    print(f'Amount of requests: {len(dataset_inference_requests)}')
    print(f'Request length limit {length_limit}')
    print('')
    inference_address = inference_parameters['address']
    inference_path = inference_parameters['path']
    prompt_lengths = []
    dataset_metadata = []
    synthetic_dataset = []
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
                    effiency_metrics = route_output['efficiency_metrics']
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
                    request_times.append(request_total_time)
                    synthetic_dataset.append(generated_data)
                    gathered_metrics.append(effiency_metrics)
            else:
                print('Request fail')
        print('')

    length_mean = statistics.mean(prompt_lengths)
    length_median = statistics.median(prompt_lengths)

    print(f'Max prompt length|{max(prompt_lengths)}')
    print(f'Min prompt length|{min(prompt_lengths)}')
    print(f'Mean prompt length|{length_mean}')
    print(f'Median prompt length|{length_median}')

    process_end_time = t.time()
    process_total_time = round(process_end_time-process_time_start,5)
    print(f'Spent seconds on processing: {process_total_time}')
    return synthetic_dataset, gathered_metrics, request_times, process_total_time

def generate_separate_output(
    output: str
) -> any:
    try:
        import re
        import json
    except ImportError as e:
        raise ImportError("generator/use failed to import", e)

    json_pattern = re.compile(r'```json\s*(.*?)\s*```', re.DOTALL | re.IGNORECASE)
    match = json_pattern.search(output)
    
    markdown_text = None
    parsed_json = None
    if match:
        # Extract the JSON string group
        json_str = match.group(1)
        
        # Remove the JSON block from the original text to isolate the Markdown
        # re.sub replaces the entire matched block with an empty string or newline
        markdown_text = json_pattern.sub('', output).strip()

        try:
            # Parse the extracted string into a Python object
            parsed_json = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Extracted text is not valid JSON: {e}")
            
    return markdown_text, parsed_json

def generate_process_data(
    model_outputs: list,
    gathered_metrics: list,
    request_times: list
):
    try:
        import pandas as pd
        from ..generator.use import generate_separate_output
        import copy
    except ImportError as e:
        raise ImportError("generator/use failed to import", e)
    # model name 
    # data type

    dataset_df_temp = pd.DataFrame(gathered_metrics)
    expanded_df = pd.json_normalize(dataset_df_temp['raw_token_counts'])
    df_final = pd.concat([dataset_df_temp.drop(columns = 'raw_token_counts'), expanded_df], axis = 1)
    df_final['times'] = request_times

    output_data_list = []
    for output in model_outputs:
        output_markdown, output_json = generate_separate_output(
            output = output
        )
        print(output)
        print(output_json)

        if not output_markdown is None or not output_json is None:
            if '</think>' in output_markdown:
                output_markdown = output_markdown.replace('</think>', '')

            output_json['thinking'] = output_markdown
            output_data_list.append(output_json)
        #df_final['thinking'] = output_markdown
        

        #print(output_markdown)
        #print(output_json)
        #break
    #df_final['outputs'] = model_outputs
    #df_final['times'] = request_times

    output_df = pd.json_normalize(output_data_list)

    print(output_df)

    return df_final
    
   