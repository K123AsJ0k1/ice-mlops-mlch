
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
        'thinking-text': thinking_text,
        'main-content': main_content,
        **parsed_sections
    }

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
    question_type_index = {}
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

                for i in range(0, metadata['amount']):
                    data_type = name.split('-')[1]
                    filled_prompt['metadata'] = {
                        'part': expectations_data['part'],
                        'chapter': expectations_data['chapter'],
                        'idx': expectations_data['idx'],
                        'characters': expectations_data['characters'],
                        'relevance': expectations_data['relevance'],
                        'weights': expectations_data['weights'],
                        'data-type': data_type,
                        'request-index': request_index,
                        'question-index': question_type_index[data_type]
                    }

                    for prompt in filled_prompt['prompt']:
                        key_name = f'{prompt['role']}-prompt-length'
                        filled_prompt['metadata'][key_name] = len(prompt['content'])
                    question_type_index[data_type] += 1
                    inference_requests.append(filled_prompt)
                    request_index += 1
    return inference_requests

def generator_send_requests(
    inference_requests: list,
    length_limit: int
):

