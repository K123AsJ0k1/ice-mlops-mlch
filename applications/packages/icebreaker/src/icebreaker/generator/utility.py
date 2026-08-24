
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
'''
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
'''