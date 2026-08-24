def judge_create_requests(
    rag_dataset: any,
    truth_dataset: any,
    run_data: any,
    prompt_parameters: any,
    dataset_name: str,
    target_model: str,
    prompt_type: str,
    question_column: str,
    answer_column: str,
    join_prompts: bool
):
    try:
        import re
    except ImportError as e:
        raise ImportError("assistant/use failed to import", e)

    print('Creating assistant requests')
    inference_requests = []
    
    assistant_run_outputs = run_data['outputs']['assistant']
    assistant_run_requests = run_data['requests']['assistant']
    assistant_run_metrics = run_data['metrics']['assistant']
    #print('asd')
    accepted_outputs = assistant_run_outputs['accept']
    refused_outputs = assistant_run_outputs['refuse']['guard']

    accepted_requests = assistant_run_requests['accept']
    refused_requests = assistant_run_requests['refuse']
    #print('asd')
    accepted_metrics = assistant_run_metrics['accept']
    refused_metrics = assistant_run_metrics['refuse']
    
    joined_outputs = accepted_outputs + refused_outputs
    joined_requests = accepted_requests + refused_requests
    joined_metrics = accepted_metrics + refused_metrics
    #print('asd')
    case_idx = 0
    for output in joined_outputs: 
        case_request = joined_requests[case_idx]
        question_type = joined_metrics[case_idx]['question-type']
        question_index = case_request['question-index']
        target_text = truth_dataset[answer_column][question_index]
        query_text = truth_dataset[question_column][question_index]
        
        replacer_dict = {
            'TARGET': target_text,
            'QUERY': query_text,
            'OUTPUT': output
        }

        if 'synth' in prompt_type:
            row_idx = truth_dataset['row-index'][question_index]
            replacer_dict['CONTENT'] = rag_dataset['content'][row_idx]

        temperature = prompt_parameters[prompt_type]['temperature'][target_model]
        top_p = prompt_parameters[prompt_type]['top-p'][target_model]
        max_tokens = prompt_parameters[prompt_type]['max-tokens'][target_model]

        system_prompt = prompt_parameters[prompt_type]['system-prompt']
        user_template = prompt_parameters[prompt_type]['user-template']
        
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
        # join prompt type and request type
        used_question_type = question_type + '-' + prompt_type
        inference_requests.append({
            'dataset-name': dataset_name,
            'case-index': case_idx,
            'question-type': used_question_type,
            'question-index': question_index,
            'messages': sent_messages,
            'system-prompt-length': system_prompt_length,
            'user-prompt-length': user_prompt_length,
            'target-model': target_model,
            'temperature': temperature,
            'top-p': top_p,
            'max-tokens': max_tokens
        })
        case_idx += 1
    print(f'Amount of requests: {len(inference_requests)}')
    return inference_requests

def judge_generate_answers(
    dataset_inference_requests: list,
    request_keys: dict,
    length_limit: int,
    inference_parameters: any,
    request_categories: list,
    debug_prints: bool
) -> dict:
    try:
        import time as t
        import statistics
        from ..assistant.utility import assistant_run_inference
        from ..judge.utility import judge_extract_output
    except ImportError as e:
        raise ImportError("assistant/use failed to import", e)
    process_time_start = t.time()
    print('Getting answers')
    print(f'Request length limit {length_limit}')
    print('')
    
    run_data = {
        'requests': [],
        'outputs': {
            'model': [],
            'score': []
        },
        'metrics': [],
        'request-times': [],
        'prompt-lengths':{
            'system': [],
            'user': []
        },
        'execution-times': [],
        'stats': {}
    }
    
    for inference_requests in dataset_inference_requests:
        execution_time_start = t.time()
        judge_request = {}
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
                run_data['prompt-lengths']['system'].append(system_prompt_length)
            if 0 < user_prompt_length:
                run_data['prompt-lengths']['user'].append(user_prompt_length)

            print('Judge print:')
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
                judge_request[key] = inference_requests[key]

            answer_metadata = {
                'dataset': dataset_name,
                'case-index': case_index,
                'question-type': question_type,
                'question-index': question_index,
                'category': category_type,
                'system-prompt-length': system_prompt_length,
                'user-prompt-length': user_prompt_length,
            }

            judge_inference_tuple = assistant_run_inference(
                inference_address = inference_parameters['judge']['address'],
                inference_path = inference_parameters['judge']['path'],
                sent_request = judge_request
            )

            judge_output = judge_inference_tuple[0]
            judge_merged_data = answer_metadata | judge_inference_tuple[1]

            judge_score = judge_extract_output(
                output = judge_output
            )

            print('Judge output score:')
            try:
                print(f'Reasoning|{judge_score['reasoning']}') 
                print(f'Correctness|{judge_score['correctness']}') 
                if 'synth' in question_type:
                    print(f'Faithfulness|{judge_score['faithfulness']}') 
                print(f'Relevance|{judge_score['relevance']}') 
            except Exception as e:
                pass

            run_data['requests'].append(inference_requests)
            run_data['outputs']['model'].append(judge_output)
            run_data['outputs']['score'].append(judge_score)
            run_data['metrics'].append(judge_merged_data)
            run_data['request-times'].append(judge_inference_tuple[2])
        execution_end_time = t.time()
        execution_total_time = round(execution_end_time-execution_time_start,5)
        run_data['execution-times'].append(execution_total_time)
        print(f'Spent seconds on execution: {execution_total_time}')
        print('')

    for key, value in run_data['prompt-lengths'].items():
        max_prompt_length = max(value)
        min_prompt_length = min(value)
        mean_prompt_length = statistics.mean(value)
        median_prompt_length = statistics.median(value)
        print(f'Prompt role|{key}')
        print(f'Max prompt length|{max_prompt_length}')
        print(f'Min prompt length|{min_prompt_length}')
        print(f'Mean prompt length|{mean_prompt_length}')
        print(f'Median prompt length|{median_prompt_length}')
        stat_key = f'{key}-prompt'
        run_data['stats'][stat_key] = {
            'max': max_prompt_length,
            'min': min_prompt_length,
            'mean': mean_prompt_length,
            'median': median_prompt_length
        }

    process_end_time = t.time()
    process_total_time = round(process_end_time-process_time_start,5)
    print(f'Spent seconds on processing: {process_total_time}')
    print('') 
    run_data['stats']['process-total-time'] = process_total_time
    
    return run_data

def judge_print_answers(
    run_data: dict
):
    run_requests = run_data['requests']
    run_outputs = run_data['outputs']['model']
    run_scores = run_data['outputs']['score']
    run_metrics = run_data['metrics']
    idx = 0
    print('START ANSWERS')
    print(f'Amount|{len(run_requests)}')
    for judge_request in run_requests:
        case_metrics = run_metrics[idx]
        case_output = run_outputs[idx]
        case_score = run_scores[idx]
        question_index = judge_request['question-index']
        
        dataset_name = judge_request['dataset-name']
        case_index = judge_request['case-index']
        question_type = judge_request['question-type']
        category_type = case_metrics['category']
        
        question_index = question_index + 1
        messages = judge_request['messages']
        system_prompt_length = judge_request['system-prompt-length']
        user_prompt_length = judge_request['user-prompt-length']
        target_model = judge_request['target-model']
        temperature = judge_request['temperature']
        top_p = judge_request['top-p']
        max_tokens = judge_request['max-tokens']

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
        print('==========')
        # Show format and type
        print('Judge prompts:')
        for message in messages:
            prompt_role = message['role']
            prompt_content = message['content']

            print(f'Role|{prompt_role}')
            print('Prompt:')
            print(prompt_content)
        print('==========')
        print('Answer:')
        print(case_output)
        print('==========')
        print('Output:')
        print(case_output)
        print('==========')
        print('Scores:')
        print(case_score)
        print('==========')
        print('')
        idx += 1

def judge_produce_answers(
    rag_dataset: any,
    truth_dataset: any,
    assistant_run_data: any,
    judge_prompts: any,
    dataset_name: str,
    target_model: str,
    prompt_type: str,
    question_column: str,
    answer_column: str,
    category_column: str,
    join_prompts: bool,
    request_keys: list,
    length_limit: int,
    inference_parameters: any
):
    try:
        from ..judge.use import judge_create_requests, judge_generate_answers, judge_print_answers
    except ImportError as e:
        raise ImportError("assistant/use failed to import", e)

    judge_requests = judge_create_requests(
        rag_dataset = rag_dataset,
        truth_dataset = truth_dataset,
        run_data = assistant_run_data,
        prompt_parameters = judge_prompts,
        dataset_name = dataset_name,
        target_model = target_model,
        prompt_type = prompt_type,
        question_column = question_column,
        answer_column = answer_column,
        join_prompts = join_prompts
    )

    judge_run_data = judge_generate_answers(
        dataset_inference_requests = judge_requests,
        request_keys = request_keys,
        length_limit = length_limit,
        inference_parameters = inference_parameters,
        request_categories = truth_dataset[category_column],
        debug_prints = False
    )
    
    try:
        judge_print_answers(
            run_data = judge_run_data 
        )
    except Exception as e:
        print(e)
        pass
    
    return judge_run_data 