
def generator_create_requests(
    swift_client: any,
    storage_parameters: any,
    dataset_paths: list,
    ranking_parameters: any,
    target_model: str,
    prompt_parameters: any,
    data_ratio: any,
    join_prompts: bool
):
    try:
        from ..objects.use import objects_get_data
        import re
        from ..search.utility import search_process_dataset
    except ImportError as e:
        raise ImportError("generator/ failed to import", e)

    print('Creating inference requests')
    inference_requests = []
    request_index = 0
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

        _, relevant_weights, _ = search_process_dataset(
            target_df = target_df,
            group_columns = ranking_parameters['group-columns'],
            value_column = ranking_parameters['value-column'],
            relevance_column = ranking_parameters['relevance-column'],
            query_column = ranking_parameters['query-column']
        )

        for row_idx, (_, row) in enumerate(target_df.iterrows()):
            if row['chapter'] == 0:
                continue
            valid_data_rows[dataset_name] += 1  
            
            replacer_dict = {
                'CONTENT': row['content']
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
                        'chunk-part': row['part'],
                        'chunk-chapter': row['chapter'],
                        'chunk-idx': row['idx'],
                        'chunk-characters': row['characters'],
                        'chunk-relevance': row['relevance'],
                        'chunk-topic': row['topic'],
                        'chunk-relevant-weights': relevant_weights[row_idx],
                        'request-index': request_index,
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
            request_index += 1
    print('')
    print('Valid cases per dataset')
    for key, value in valid_data_rows.items():
        print(f'{key}|{value}')
    print(f'Amount of requests: {len(inference_requests)}')
    return inference_requests

def generator_create_answers(
    dataset_inference_requests: list,
    request_keys: dict,
    length_limit: int,
    inference_parameters: any,
    debug_prints: bool
) -> dict:
    try:
        import statistics
        import time as t
        from ..ray.utility import ray_run_inference
        from ..generator.utility import generator_extract_output
    except ImportError as e:
        raise ImportError("generator/ failed to import", e)
    process_time_start = t.time()
    print('Creating dataset')
    print(f'Request length limit {length_limit}')
    print('')

    run_data = {
        'requests': [],
        'outputs': {
            'model': [],
            'data': []
        },
        'metrics': [],
        'request-times': [],
        'prompt-lengths': {
            'system': [],
            'user': []
        },
        'execution-times': [],
        'stats': {}
    }

    for inference_requests in dataset_inference_requests:
        execution_time_start = t.time()
        generator_request = {}
        dataset_name = inference_requests['dataset-name']
        chunk_part = inference_requests['chunk-part']
        chunk_chapter = inference_requests['chunk-chapter']
        chunk_idx = inference_requests['chunk-idx']
        chunk_characters = inference_requests['chunk-characters']
        chunk_relevance = inference_requests['chunk-relevance']
        chunk_topic = inference_requests['chunk-topic']
        chunk_relevant_weights = inference_requests['chunk-relevant-weights']
        request_index = inference_requests['request-index'] + 1
        question_type = inference_requests['question-type']
        question_index = inference_requests['question-index'] + 1

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

            print(f'Dataset|{dataset_name}')
            print(f'Part|{chunk_part}')
            print(f'Chapter|{chunk_chapter}')
            print(f'Index|{chunk_idx}')
            print(f'Characters|{chunk_characters}')
            print(f'Request|{request_index}')
            print(f'Question type|{question_type}')
            print(f'Question index|{question_index}')
            print(f'System prompt length|{system_prompt_length}')
            print(f'User prompt length|{user_prompt_length}')
            print(f'Model|{target_model}')
            print(f'Temperature|{temperature}')
            print(f'Top-p|{top_p}')
            print(f'Max tokens|{max_tokens}') 

            for key in request_keys:
                generator_request[key] = inference_requests[key]

            answer_metadata = {
                'dataset': dataset_name,
                'chunk-part': chunk_part,
                'chunk-chapter': chunk_chapter,
                'chunk-idx': chunk_idx,
                'chunk-characters': chunk_characters,
                'chunk-relevance': chunk_relevance,
                'chunk-topic': chunk_topic,
                'chunk-relevant-weights': chunk_relevant_weights,
                'request-index': request_index,
                'question-type': question_type,
                'question-index': question_index,
                'system-prompt-length': system_prompt_length,
                'user-prompt-length': user_prompt_length,
            }

            generator_inference_tuple = ray_run_inference(
                inference_address = inference_parameters['generator']['address'],
                inference_path = inference_parameters['generator']['path'],
                sent_request = generator_request
            )

            generator_output = generator_inference_tuple[0]
            generator_merged_data = answer_metadata | generator_inference_tuple[1]

            generator_data = generator_extract_output(
                output = generator_output
            )

            run_data['requests'].append(inference_requests)
            run_data['outputs']['model'].append(generator_output)
            run_data['outputs']['data'].append(generator_data)
            run_data['metrics'].append(generator_merged_data)
            run_data['request-times'].append(generator_inference_tuple[2])
        execution_end_time = t.time()
        execution_total_time = round(execution_end_time-execution_time_start,5)
        run_data['execution-times'].append(execution_total_time)
        print(f'Spent seconds on execution: {execution_total_time}')
        print('')

    try:
        for key, value in run_data['prompt-lengths'].items():
            if 0 < len(value):
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
    except Exception as e:
        print(e)

    process_end_time = t.time()
    process_total_time = round(process_end_time-process_time_start,5)
    print(f'Spent seconds on processing: {process_total_time}')
    print('') 
    run_data['stats']['process-total-time'] = process_total_time
    
    return run_data

def generator_print_answers(
    run_data: dict
):
    run_requests = run_data['requests']
    run_model_outputs = run_data['outputs']['model']
    run_model_data = run_data['outputs']['data']
    run_metrics = run_data['metrics']
    print('START ANSWERS')
    print(f'Amount|{len(run_requests)}')
    idx = 0
    for judge_request in run_requests:
        case_metrics = run_metrics[idx]
        case_output = run_model_outputs[idx]
        case_data = run_model_data [idx]
        question_index = judge_request['question-index']
        
        dataset_name = judge_request['dataset-name']
        request_index = judge_request['request-index']
        question_type = judge_request['question-type']
        
        question_index = question_index + 1
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
        print(f'Question index|{question_index}')
        print(f'System prompt length|{system_prompt_length}')
        print(f'User prompt length|{user_prompt_length}')
        print(f'Model|{target_model}')
        print(f'Temperature|{temperature}')
        print(f'Top-p|{top_p}')
        print(f'Max tokens|{max_tokens}') 
        print('')
        print('==========')
        # Show format and type
        print('Generator prompts:')
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
        print('Data:')
        print(case_data)
        print('==========')
        print('')
        idx += 1

def generator_produce_answers(
    swift_client: any,
    storage_parameters: any,
    dataset_paths: list,
    ranking_parameters: any,
    target_model: str,
    prompt_parameters: any,
    data_ratio: any,
    join_prompts: bool,
    request_keys: dict,
    length_limit: int,
    request_start: int,
    request_end: int,
    inference_parameters: any,
    debug_prints: bool
):
    generator_requests = generator_create_requests(
        swift_client = swift_client,
        storage_parameters = storage_parameters,
        dataset_paths = dataset_paths,
        ranking_parameters = ranking_parameters,
        target_model = target_model,
        prompt_parameters = prompt_parameters,
        data_ratio = data_ratio,
        join_prompts = join_prompts
    )

    if 0 < request_end:
        generator_requests = generator_requests[request_start:request_end]

    generator_run_data = generator_create_answers(
        dataset_inference_requests = generator_requests,
        request_keys = request_keys,
        length_limit = length_limit,
        inference_parameters = inference_parameters,
        debug_prints = debug_prints
    )

    try:
        generator_print_answers(
            run_data = generator_run_data
        )
    except Exception as e:
        print(e)
    
    return generator_run_data