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
        raise ImportError("judge/use failed to import", e)
 
    print('Creating judge requests')
    inference_requests = []
    
    assistant_run_outputs = run_data['outputs']['assistant']
    assistant_run_metrics = run_data['metrics']['assistant']
    
    accepted_outputs = assistant_run_outputs['accept']
    refused_outputs = assistant_run_outputs['refuse']['guard']
    #print('asd')
    accepted_metrics = assistant_run_metrics['accept']
    refused_metrics = assistant_run_metrics['refuse']
    
    joined_outputs = accepted_outputs + refused_outputs
    joined_metrics = accepted_metrics + refused_metrics
    
    question_idx = 0
    for output in joined_outputs: 
        # This is caused by the earlier bug
        output_metrics = joined_metrics[question_idx]
        if 'request-index' in output_metrics:
            request_idx = output_metrics['request-index'] - 1
            #print(request_idx)
            assistant_variant = joined_metrics[question_idx]['assistant-variant']
            question_type = joined_metrics[question_idx]['question-type']
            target_text = truth_dataset[answer_column][request_idx]
            query_text = truth_dataset[question_column][request_idx]
            
            replacer_dict = {
                'TARGET': target_text,
                'QUERY': query_text,
                'OUTPUT': output
            }

            if 'synthetic' in prompt_type:
                # Misalinged content
                chunk_idx = truth_dataset['chunk-idx'][request_idx]
                replacer_dict['CONTENT'] = rag_dataset['content'][chunk_idx]

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
            
            used_question_type = f'{assistant_variant}-{question_type}-{prompt_type}'
            inference_requests.append({
                'dataset-name': dataset_name,
                'request-index': request_idx,
                'question-type': used_question_type,
                'question-index': question_idx,
                'messages': sent_messages,
                'system-prompt-length': system_prompt_length,
                'user-prompt-length': user_prompt_length,
                'target-model': target_model,
                'temperature': temperature,
                'top-p': top_p,
                'max-tokens': max_tokens
            })
            question_idx += 1
    print(f'Amount of requests: {len(inference_requests)}')
    return inference_requests

def judge_generate_answers(
    dataset_inference_requests: list,
    request_keys: dict,
    length_limit: int,
    inference_parameters: any,
    debug_prints: bool
) -> dict:
    try:
        import time as t
        from ..ray.utility import ray_run_inference
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
        'request-times-sec': [],
        'prompt-lengths':{
            'system': [],
            'user': []
        },
        'execution-times-sec': [],
        'stats': {}
    }
    
    for inference_requests in dataset_inference_requests:
        execution_time_start = t.time()
        judge_request = {}
        dataset_name = inference_requests['dataset-name']
        request_index = inference_requests['request-index']
        question_type = inference_requests['question-type']

        system_prompt_length = inference_requests['system-prompt-length']
        user_prompt_length = inference_requests['user-prompt-length']
        target_model = inference_requests['target-model']
        temperature = inference_requests['temperature']
        top_p = inference_requests['top-p']
        max_tokens = inference_requests['max-tokens']
        used_context = system_prompt_length + user_prompt_length
        if used_context < length_limit:
            if 0 < system_prompt_length:
                run_data['prompt-lengths']['system'].append(system_prompt_length)
            if 0 < user_prompt_length:
                run_data['prompt-lengths']['user'].append(user_prompt_length)

            print('Judge print:')
            print(f'Dataset|{dataset_name}')
            print(f'Request|{request_index + 1}')
            print(f'Question type|{question_type}')
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
                'request-index': request_index,
                'question-type': question_type,
                'system-prompt-length': system_prompt_length,
                'user-prompt-length': user_prompt_length,
            }

            judge_inference_tuple = ray_run_inference(
                inference_address = inference_parameters['judge']['address'],
                inference_path = inference_parameters['judge']['path'],
                sent_request = judge_request
            )

            judge_output = judge_inference_tuple[0]
            judge_merged_data = answer_metadata | judge_inference_tuple[1]

            judge_score = judge_extract_output(
                output = judge_output
            )
            judge_score['question-type'] = question_type

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
            run_data['request-times-sec'].append(judge_inference_tuple[2])
        execution_end_time = t.time()
        execution_total_time = round(execution_end_time-execution_time_start,5)
        run_data['execution-times-sec'].append(execution_total_time)
        print(f'Spent seconds on execution: {execution_total_time}')
        print('')

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
    idx = 0
    print('START ANSWERS')
    print(f'Amount|{len(run_requests)}')
    for judge_request in run_requests:
        case_output = run_outputs[idx]
        case_score = run_scores[idx]
        
        dataset_name = judge_request['dataset-name']
        request_index = judge_request['request-index']
        question_type = judge_request['question-type']
        question_index = judge_request['question-index']
        
        messages = judge_request['messages']
        system_prompt_length = judge_request['system-prompt-length']
        user_prompt_length = judge_request['user-prompt-length']
        target_model = judge_request['target-model']
        temperature = judge_request['temperature']
        top_p = judge_request['top-p']
        max_tokens = judge_request['max-tokens']

        print(f'Dataset|{dataset_name}')
        print(f'Request|{request_index}')
        print(f'Question type|{question_type}')
        print(f'Question index|{question_index + 1}')
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
    join_prompts: bool,
    request_keys: list,
    length_limit: int,
    inference_parameters: any,
    summary_target_keys: list,
    summary_relevant_key_columns: dict,
    summary_wanted_stats: list,
    summary_key_group_column: dict
):
    try:
        from ..judge.use import judge_create_requests, judge_generate_answers, judge_print_answers
        from ..evalution.use import evalution_nested_metrics
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
        debug_prints = False
    )
    
    try:
        judge_print_answers(
            run_data = judge_run_data 
        )
    except Exception as e:
        print(e)

    try:
        # This removes the process time
        nested_stats = evalution_nested_metrics(
            run_data = judge_run_data,
            target_keys = summary_target_keys,
            relevant_key_columns = summary_relevant_key_columns,
            wanted_stats = summary_wanted_stats,
            key_group_column = summary_key_group_column
        )

        judge_run_data['stats'] = judge_run_data['stats'] | nested_stats
    except Exception as e:
        print(e)

    return judge_run_data 