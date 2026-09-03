def judge_extract_output(
    output: str
):
    try:
        import re
        import json
    except ImportError as e:
        raise ImportError("judge/utility failed to import", e)
    
    json_match = re.search(r"\{.*\}", output, re.DOTALL)
    if not json_match:
        return {
            'reasoning': 'Failed to extract JSON from guardrail output', 
            'correctness': 0,
            'faithfulness': 0,
            'relevance': 0,
        }

    json_str = json_match.group(0)

    try:
        data = json.loads(json_str)
        return data
    except Exception as e:
        return {
            'reasoning': 'Malformed JSON returned by guardrail', 
            'correctness': 0,
            'faithfulness': 0,
            'relevance': 0,
        }

def judge_evalute_models(
    model_run_data: dict,
    target_keys: list,
    relevant_key_columns: dict,
    relevant_column_prefix: dict
):
    try:
        from ..misc.dict import get_dict_value
        import pandas as pd
    except ImportError as e:
        raise ImportError("evaluation/use failed to import", e)
    
    #collected_metrics = {}
    metrics_rows = []
    metrics_columns = []
    for judge_name, judged in model_run_data.items():
        for judged_name, data in judged.items():
            #root_name = f'{judge_name}-{judged_name}'
            for data_name, data_value in data.items():
                metrics_row = []
                for record in data_value['records']:
                    for target in target_keys:
                        data = get_dict_value(
                            target_dict = record,
                            key_path = target,
                            separator = '|'
                        )
                        
                        metric_key = target.split('|')[-1]
                        relevant_columns = relevant_key_columns[metric_key]
                        for key, value in data.items():
                            if key in relevant_columns:
                                value_column = f'{relevant_column_prefix[metric_key]}-{key}'
                                if not value_column in metrics_columns:
                                    metrics_columns.append(value_column)
                                metrics_row.append(value)
                metrics_rows.extend(metrics_row)
    print(metrics_columns)
    collected_df = pd.DataFrame(metrics_rows)
           
    return collected_df
