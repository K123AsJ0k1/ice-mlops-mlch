
def generator_process_references(
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
    
def generator_process_paths(
    used_paths: str
) -> any:
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("generator/use failed to import", e)
    
    if 'N/A' in used_paths:
        return pd.NA

    if not '(' in used_paths or not ')' in used_paths:
        if './docs/config/settings.yaml' in used_paths:
            return pd.NA

        if './' in used_paths:
            return used_paths
    
    if '(' in used_paths or ')' in used_paths:
        if './docs/config/settings.yaml' in used_paths:
            return pd.NA

        return used_paths.replace("(", "").replace(")", "")

    return 'Hallucinated'

def generator_process_category(
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

def generator_parse_output(
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
        'reasoning': {
            'thinking_process': thinking_text
        },
        'response': main_content,
        **parsed_sections
    }

def generator_extract_output(
    output: str
):
    output_dict = generator_parse_output(
        text = output
    )
    
    if 'type' in output_dict:
        if output_dict['type'] == 'factual' or output_dict['type'] == 'synthesis':
            if 'relevant-used-references' in output_dict and 'relevant-used-paths' in output_dict:
                
                checked_references = generator_process_references(
                    used_references = output_dict['relevant-used-references']
                )
                
                output_dict['relevant-used-references'] = checked_references
                checked_paths = generator_process_paths(
                    used_paths = output_dict['relevant-used-paths']
                )
                
                output_dict['relevant-used-paths'] = checked_paths

        if output_dict['type'] == 'negative':
            if 'ground-truth-answer' in output_dict:
                
                category_data = generator_process_category(
                    answer = output_dict['ground-truth-answer']
                )
                
                for key, value in category_data.items():
                    output_dict[key] = value
    return output_dict

def generator_process_data(
    run_data: any
) -> any:
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("generator/utility failed to import", e)

    run_requests = run_data['requests']
    run_model_output = run_data['outputs']['model']
    run_data_output = run_data['outputs']['data']
    run_metrics = run_data['metrics']
    run_request_times = run_data['request-times']
    run_execution_times = run_data['execution-times']

    expanded_df_1 = pd.DataFrame(run_requests)
    expanded_df_1['model-output'] = run_model_output
    expanded_df_2 = pd.DataFrame(run_data_output)  
    expanded_df_3 = pd.DataFrame(run_metrics)
    expanded_df_3['request-time-sec'] = run_request_times
    expanded_df_3['execution-time-sec'] = run_execution_times

    preprocess_df = pd.concat([expanded_df_1, expanded_df_2, expanded_df_3], axis = 1)
    preprocess_df = preprocess_df.loc[:, ~preprocess_df.columns.duplicated()]
    preprocess_df = preprocess_df.convert_dtypes()

    return preprocess_df

def generator_create_requests(
    mlflow_client: any,
    dataset_ids: list,
    prompts: dict
):
    from ..mlflow.use import mlflow_get_dataset, mlflow_get_prompt

    request_index = 0
    prompt_variant_index = {}
    inference_requests = []
    for dataset_id in dataset_ids:
        dataset_df = mlflow_get_dataset(
            mlflow_client = mlflow_client,
            dataset_id = dataset_id
        )  
        
        for row in dataset_df.to_dict(orient = 'records'):
            for name, metadata in prompts.items():
                expectations_data = row['expectations']
                filled_prompt = mlflow_get_prompt(
                    mlflow_client = mlflow_client,
                    prompt_name = name,
                    prompt_version = metadata['version'],
                    prompt_replacements = {
                        'content': expectations_data['ground_truth']
                    }
                )

                prompt_variant = name.split('-')[1]
                if not prompt_variant in prompt_variant_index:
                    prompt_variant_index[prompt_variant] = 1

                for i in range(0, metadata['amount']):
                    filled_prompt['metadata'] = {
                        'dataset-id': dataset_id,
                        'part': expectations_data['part'],
                        'chapter': expectations_data['chapter'],
                        'idx': expectations_data['idx'],
                        'characters': expectations_data['characters'],
                        'relevance': expectations_data['relevance'],
                        'weights': expectations_data['weights'],
                        'prompt-variant': prompt_variant,
                        'request-index': request_index,
                        'variant-index': prompt_variant_index[prompt_variant]
                    }

                    for prompt in filled_prompt['prompt']:
                        key_name = f'{prompt['role']}-prompt-length'
                        filled_prompt['metadata'][key_name] = len(prompt['content'])
                    
                    prompt_variant_index[prompt_variant] += 1
                    inference_requests.append(filled_prompt)
                    request_index += 1
    return inference_requests

def generator_send_requests(
    mlflow_client: any,
    experiment_id: str,
    inference_requests: list,
    length_limit: int,
    trace_name: str,
    trace_attributes: dict,
    trace_tags: dict,
    request_limit: int,
    inference_parameters: dict,
    debug_prints: bool
):
    try:
        import mlflow
        from ..mlflow.use import mlflow_create_trace, mlflow_end_trace
        from ..mlflow.utility import mlflow_token_usage, mlflow_llm_cost, mlflow_llm_effiency
        from ..ray.utility import ray_run_inference
        from ..generator.utility import generator_extract_output
    except ImportError as e:
        raise ImportError("evaluation/pipe failed to import", e)

    mlflow.set_experiment(
        experiment_id = experiment_id
    )

    generator_data = {
        'parameters': trace_attributes,
        'inputs': [],
        'metrics': [],
        'outputs': []
    }
    sent_requests = 0
    for request in inference_requests:
        if request_limit <= sent_requests:
            break

        used_context = 0
        for key, value in request['metadata'].items():
            if 'prompt-length' in key:
                used_context += value

        if used_context < length_limit:
            sent_prompt = request['prompt']
            used_config = request['config']
            prompt_metadata = request['metadata']
            prompt_metadata = prompt_metadata | used_config
            prompt_metadata['request-limit'] = request_limit

            trace_input = {
                'messages': sent_prompt
            }

            generator_data['inputs'].append(trace_input)
        
            root_span = mlflow_create_trace(
                mlflow_client = mlflow_client,  
                trace_name = trace_name,
                experiment_id = experiment_id,
                trace_attributes = trace_attributes,
                trace_tags = trace_tags,
                trace_input = trace_input
            )
            
            root_span.set_attributes({f'request.{k}': v for k, v in used_config.items()})

            generator_request = trace_input | used_config
            
            generator_payload = ray_run_inference(
                inference_address = inference_parameters['generator']['address'],
                inference_path = inference_parameters['generator']['path'],
                sent_request = generator_request
            )
            sent_requests += 1
            
            generator_metrics = generator_payload['metrics']
            generator_metadata = generator_payload['metadata']
            generator_output = generator_payload['response']

            prompt_metadata['inference-server'] = generator_metadata['inference_server']
            prompt_metadata['model-name'] = generator_metadata['used_model']

            generator_data['metrics'].append(generator_metrics)
            
            root_span.set_attributes(
                mlflow_token_usage(
                    input_tokens = generator_metrics['prompt-tokens'], 
                    output_tokens = generator_metrics['completion-tokens']
                )
            )

            input_cost = trace_attributes['ice.utilization_cost_sec'] * generator_metrics['prompt-processing-time-sec']
            output_cost = trace_attributes['ice.utilization_cost_sec'] * generator_metrics['generation-time-sec']
            
            prompt_metadata['input-cost'] = input_cost
            prompt_metadata['output-cost'] = output_cost
            prompt_metadata['total-cost'] = input_cost + output_cost

            model_name = f'{trace_attributes['llm.model_repository']}-{trace_attributes['llm.model_quantization']}'
            root_span.set_attributes(
                mlflow_llm_cost(
                    model_provider = trace_attributes['llm.inference_framework'], 
                    model_name = model_name, 
                    input_cost = input_cost, 
                    output_cost = output_cost
                )
            )
            
            root_span.set_attributes(
                mlflow_llm_effiency(
                    prompt_tokens = generator_metrics['prompt-tokens'],
                    completion_tokens = generator_metrics['completion-tokens'],
                    total_tokens = generator_metrics['total-tokens'],
                    prompt_processing_time = generator_metrics['prompt-processing-time-sec'],
                    generation_time = generator_metrics['generation-time-sec'],
                    input_tokens_per_sec = generator_metrics['input-tokens-per-sec'],
                    output_tokens_per_sec = generator_metrics['output-tokens-per-sec'],
                    total_latency = generator_metrics['total-latency-sec'],
                    time_to_first_token = generator_metrics['time-to-first-token-sec'],
                    tokens_per_second = generator_metrics['tokens-per-second'],
                    time_per_output_token = generator_metrics['time-per-output-token-sec'],
                    input_to_output_ratio = generator_metrics['input-to-output-ratio'],
                    context_window_utilization = generator_metrics['context-window-utilization-pct'],
                )
            )
            
            extracted_output = generator_extract_output(
                output = generator_output
            )

            trace_output = extracted_output | prompt_metadata

            generator_data['outputs'].append(trace_output)
            
            mlflow_end_trace(
                mlflow_client = mlflow_client,
                trace_id = root_span.trace_id,
                trace_output = trace_output
            )
    generator_data['parameters']['requests'] = sent_requests
    print('')
    if debug_prints:
        print('Data generator parameters:')
        parameters = generator_data['parameters']

        for name, value in parameters.items():
            print(f'{name}|{value}')

        print('==========')

        for i, input, in enumerate(generator_data['inputs']):
            metrics = generator_data['metrics'][i]
            output = generator_data['outputs'][i]

            print('Generator prompts:')
            for message in input['messages']:
                prompt_role = message['role']
                prompt_content = message['content']
    
                print(f'Role|{prompt_role}')
                print('Prompt:')
                print(prompt_content)

            print('==========')
        
            for name, value in metrics.items():
                print(f'{name}|{value}')

            print('==========')

            filtered_keys = [
                'reasoning',
                'response',
                'question',
                'ground-truth-answer'
            ]

            for name, value in output.items():
                if name in filtered_keys:
                    continue
                print(f'{name}|{value}')

            print('==========')
            print('Reasoning:')
            print(output['reasoning']['thinking_process'])
            print('==========')
            print('Answer:')
            print(output['response'])
            print('==========')
        
    return generator_data

def generator_format_data(
    generator_data: any,
    metric_columns: list
) -> any:
    try:
        import pandas as pd
        from ..misc.dict import flatten_nested_dict
        from ..pd_stats.utility import pandas_get_p95, pandas_get_p99
    except ImportError as e:
        raise ImportError("evaluation/use failed to import", e)
    
    formatted_table = {}
    formatted_metrics = {}
    
    for name, data in generator_data.items():
        if not name == 'parameters':
            for data_dict in data:
                for key, value in data_dict.items():
                    if not key in formatted_table:
                        formatted_table[key] = []
                    formatted_table[key].append(value)
         
    created_dataframe = pd.DataFrame(formatted_table)   

    metric_dict = created_dataframe[metric_columns].agg([
        'mean', 
        'std', 
        'median', 
        pandas_get_p95, 
        pandas_get_p99, 
        'min', 
        'max'
    ]).to_dict()
    
    formatted_metrics = flatten_nested_dict(
        target_dict = metric_dict,
        parent_key = '',
        seperator = '-'
    )

    formatted_parametes = {}
    for key, value in generator_data['parameters'].items():
        fixed_name = key.split('.')[-1]
        formatted_parametes[fixed_name] = value
    
    return {
        'parameters': formatted_parametes,
        'tables': created_dataframe,
        'metrics': formatted_metrics
    }