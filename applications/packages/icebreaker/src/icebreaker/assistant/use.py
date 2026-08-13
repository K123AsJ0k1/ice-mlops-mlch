def assistant_create_requests(
    target_df: any,
    prompt_parameters: any,
    dataset_name: str,
    target_model: str,
    data_ratio: any,
    join_prompts: bool
):
    try:
        import re
    except ImportError as e:
        raise ImportError("assistant/use failed to import", e)

    print('Creating assistant requests')
    inference_requests = []
    case_idx = 0
    question_type_idx = {}
    for _, row in target_df.iterrows(): 
       
        replacer_dict = {
            'QUERY': row['question']
        }
        for data_type, wanted_amount in data_ratio.items():
            if not data_type in question_type_idx:
                question_type_idx[data_type] = 0
            
            system_prompt = prompt_parameters[data_type]['system-prompt']
            user_template = prompt_parameters[data_type]['user-template']
            
            temperature = prompt_parameters[data_type]['temperature'][target_model]
            top_p = prompt_parameters[data_type]['top-p'][target_model]
            max_tokens = prompt_parameters[data_type]['max-tokens'][target_model]

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
                    'case-index': case_idx,
                    'question-type': data_type,
                    'question-index': question_type_idx[data_type],
                    'messages': sent_messages,
                    'system-prompt-length': system_prompt_length,
                    'user-prompt-length': user_prompt_length,
                    'target-model': target_model,
                    'temperature': temperature,
                    'top-p': top_p,
                    'max-tokens': max_tokens
                })
                question_type_idx[data_type] += 1
        case_idx += 1
    print(f'Amount of requests: {len(inference_requests)}')
    return inference_requests

def assistant_generate_answers(
    dataset_inference_requests: list,
    request_keys: dict,
    length_limit: int,
    inference_parameters: any,
    request_categories: list,
    debug_prints: bool
) -> dict:
    try:
        from ..ray.use import ray_serve_route
        import statistics
        import time as t
    except ImportError as e:
        raise ImportError("assistant/use failed to import", e)
    process_time_start = t.time()
    print('Getting answers')
    print(f'Request length limit {length_limit}')
    print('')
    inference_address = inference_parameters['address']
    inference_path = inference_parameters['path']
    prompt_lengths = []
    model_outputs = []
    gathered_metrics = []
    request_times = []
    # The end dataset also required input for double checking
    # There should be columns for messages
    for inference_requests in dataset_inference_requests:
        sent_request = {}
        dataset_name = inference_requests['dataset-name']
        case_index = inference_requests['case-index'] + 1
        question_type = inference_requests['question-type']
        question_index = inference_requests['question-index']
        category_type = request_categories[question_index]
        question_index = question_index + 1
        
        system_prompt_length = inference_requests['system-prompt-length']
        user_prompt_length = inference_requests['user-prompt-length']
        target_model = inference_requests['target-model']
        temperature = inference_requests['temperature']
        top_p = inference_requests['top-p']
        max_tokens = inference_requests['max-tokens']

        if user_prompt_length < length_limit:
            if 0 < system_prompt_length:
                prompt_lengths.append(system_prompt_length)
            if 0 < user_prompt_length:
                prompt_lengths.append(user_prompt_length)

            print(f'Dataset|{dataset_name}')
            print(f'Case|{case_index}')
            print(f'Question type|{question_type}')
            print(f'Question index|{question_index}')
            print(f'Category|{category_type}')
            print(f'System prompt length|{system_prompt_length}')
            print(f'User prompt length|{user_prompt_length}')
            print(f'Model|{target_model}')
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
                    metadata = {
                        'dataset': dataset_name,
                        'case-index': case_index,
                        'question-type': question_type,
                        'question-index': question_index,
                        'category': category_type,
                        'system-prompt-length': system_prompt_length,
                        'user-prompt-length': user_prompt_length,
                    }

                    effiency_metrics = route_output['efficiency-metrics']
                    merged_data = metadata | effiency_metrics
                    model_outputs.append(generated_data)
                    gathered_metrics.append(merged_data)
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
    print('')

    general_stats = {
        'length-mean': length_mean,
        'length-median': length_median,
        'max-prompt-length': max_prompt_length,
        'min-prompt-length': min_prompt_length,
        'process-total-time': process_total_time
    }
    
    return model_outputs, gathered_metrics, request_times, general_stats

def assistant_print_answers(
    requests: list, 
    outputs: list,
    answers: list,
    categories: list
):
    for i in range(0, len(requests)):
        case_request = requests[i]
        case_output = outputs[i]

        question_index = case_request['question-index']
        case_answer = answers[question_index]
        
        dataset_name = case_request['dataset-name']
        case_index = case_request['case-index']
        question_type = case_request['question-type']
        category_type = categories[question_index]
        
        question_index = question_index  + 1
        messages = case_request['messages']
        system_prompt_length = case_request['system-prompt-length']
        user_prompt_length = case_request['user-prompt-length']
        target_model = case_request['target-model']
        temperature = case_request['temperature']
        top_p = case_request['top-p']
        max_tokens = case_request['max-tokens']

        print(f'Dataset|{dataset_name}')
        print(f'Case|{case_index}')
        print(f'Question type|{question_type}')
        print(f'Question index|{question_index}')
        print(f'Category|{category_type}')
        print(f'System prompt length|{system_prompt_length}')
        print(f'User prompt length|{user_prompt_length}')
        print(f'Model|{target_model}')
        print(f'Temperature|{temperature}')
        print(f'Top-p|{top_p}')
        print(f'Max tokens|{max_tokens}') 
        print('')
        print('---')
        # Show format and type
        print('Sent prompts')
        for message in messages:
            prompt_role = message['role']
            prompt_content = message['content']

            print(f'Role|{prompt_role}')
            print('Prompt:')
            print(prompt_content)
        print('---')
        print('Output:')
        print(case_output)
        print('---')
        print('Answer:')
        print(case_answer)
        print('---')
        print('')

def assistant_produce_answers(
    target_df: any,
    assistant_prompts: dict,
    dataset_name: str,
    target_model: str,
    request_ratio: dict,
    join_prompts: bool,
    request_keys: list,
    length_limit: int,
    inference_parameters: any,
    answer_column: str,
    category_column: str
):
    try:
        from ..assistant.use import assistant_create_requests, assistant_generate_answers, assistant_print_answers
    except ImportError as e:
        raise ImportError("assistant/use failed to import", e)

    assistant_requests = assistant_create_requests(
        target_df = target_df,
        prompt_parameters = assistant_prompts,
        dataset_name = dataset_name,
        target_model = target_model,
        data_ratio = request_ratio,
        join_prompts = join_prompts
    )

    dataset_answers = target_df[answer_column]
    dataset_categories = target_df[category_column]

    model_outputs, gathered_metrics, request_times, general_stats = assistant_generate_answers(
        dataset_inference_requests = assistant_requests,
        request_keys = request_keys,
        length_limit = length_limit,
        inference_parameters = inference_parameters,
        request_categories = dataset_categories,
        debug_prints = False
    )

    assistant_print_answers(
        requests = assistant_requests, 
        outputs = model_outputs,
        answers = dataset_answers,
        categories = dataset_categories
    )

    output_tuple = (
        assistant_requests,
        model_outputs,
        gathered_metrics,
        request_times,
        general_stats
    )

    return output_tuple