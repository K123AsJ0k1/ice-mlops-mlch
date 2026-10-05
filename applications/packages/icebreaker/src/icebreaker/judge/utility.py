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

def judge_model_report(
    metrics_df: any,
    group_columns: list,
    score_columns: list,
    effiency_columns: list
):
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("evaluation/use failed to import", e)
    
    melted = metrics_df.melt(
        id_vars = group_columns,
        value_vars = score_columns,
        var_name = 'metric',
        value_name = 'score'
    )

    index_cols = group_columns + ['metric']

    grouped_counts = pd.crosstab(
        index = [melted[col] for col in index_cols],
        columns = melted['score']
    )

    grouped_counts['pass_pct'] = (grouped_counts[1] / (grouped_counts[0] + grouped_counts[1]) * 100).round(2)
    
    efficiency_means = metrics_df.groupby(group_columns)[effiency_columns].mean().round(2)

    counts_flat = grouped_counts.reset_index()

    final_report = counts_flat.merge(efficiency_means, on = group_columns, how = 'left')

    return final_report.set_index(index_cols)

def judge_summarize_models(
    metrics_df: any,
    group_columns: list,
    score_columns: list,
    effiency_columns: list
):
    try:
        from ..judge.utility import judge_model_report
    except ImportError as e:
        raise ImportError("evaluation/use failed to import", e)

    summarizes = {}

    # format
    summarizes['format-report'] = judge_model_report(
        metrics_df = metrics_df,
        group_columns = [
            'assistant-format'
        ],
        score_columns = score_columns,
        effiency_columns = effiency_columns
    )

    summarizes['data-format-report'] = judge_model_report(
        metrics_df = metrics_df,
        group_columns = [
            'data-type',
            'assistant-format'
        ],
        score_columns = score_columns,
        effiency_columns = effiency_columns
    )

    summarizes['data-assistant-report'] = judge_model_report(
        metrics_df = metrics_df,
        group_columns = [
            'data-type',
            'assistant-used-model'
        ],
        score_columns = score_columns,
        effiency_columns = effiency_columns
    )
    
    summarizes['data-variant-report'] = judge_model_report(
        metrics_df = metrics_df,
        group_columns = [
            'data-type', 
            'assistant-variant'
        ],
        score_columns = score_columns,
        effiency_columns = effiency_columns
    )

    summarizes['data-variant-format-report'] = judge_model_report(
        metrics_df = metrics_df,
        group_columns = [
            'data-type',
            'assistant-variant',
            'assistant-format'
        ],
        score_columns = score_columns,
        effiency_columns = effiency_columns
    )

    summarizes['data-assistant-format-report'] = judge_model_report(
        metrics_df = metrics_df,
        group_columns = [
            'data-type',
            'assistant-used-model',
            'assistant-format'
        ],
        score_columns = score_columns,
        effiency_columns = effiency_columns
    )

    summarizes['data-variant-assistant-report'] = judge_model_report(
        metrics_df = metrics_df,
        group_columns = [
            'data-type', 
            'assistant-variant', 
            'assistant-used-model'
        ],
        score_columns = score_columns,
        effiency_columns = effiency_columns
    )
    
    # assistant
    summarizes['assistant-report'] = judge_model_report(
        metrics_df = metrics_df,
        group_columns = [
            'assistant-used-model'
        ],
        score_columns = score_columns,
        effiency_columns = effiency_columns
    )

    summarizes['assistant-format-report'] = judge_model_report(
        metrics_df = metrics_df,
        group_columns = [
            'assistant-used-model',
            'assistant-format'
        ],
        score_columns = score_columns,
        effiency_columns = effiency_columns
    )
    
    # variant
    summarizes['variant-report'] = judge_model_report(
        metrics_df = metrics_df,
        group_columns = [
            'assistant-variant'
        ],
        score_columns = score_columns,
        effiency_columns = effiency_columns
    )

    summarizes['variant-assistant-report'] = judge_model_report(
        metrics_df = metrics_df,
        group_columns = [
            'assistant-variant', 
            'assistant-used-model'
        ],
        score_columns = score_columns,
        effiency_columns = effiency_columns
    )   

    summarizes['variant-format-report'] = judge_model_report(
        metrics_df = metrics_df,
        group_columns = [
            'assistant-variant', 
            'assistant-format'
        ],
        score_columns = score_columns,
        effiency_columns = effiency_columns
    )  
    
    summarizes['judge-assistant-report'] = judge_model_report(
        metrics_df = metrics_df,
        group_columns = [
            'judge-used-model', 
            'assistant-used-model'
        ],
        score_columns = score_columns,
        effiency_columns = effiency_columns
    )
    
    summarizes['judge-variant-report'] = judge_model_report(
        metrics_df = metrics_df,
        group_columns = [
            'judge-used-model', 
            'assistant-variant'
        ],
        score_columns = score_columns,
        effiency_columns = effiency_columns
    )

    summarizes['judge-format-report'] = judge_model_report(
        metrics_df = metrics_df,
        group_columns = [
            'judge-used-model', 
            'assistant-format'
        ],
        score_columns = score_columns,
        effiency_columns = effiency_columns
    )
    
    summarizes['judge-variant-assistant-report'] = judge_model_report(
        metrics_df = metrics_df,
        group_columns = [
            'judge-used-model', 
            'assistant-variant', 
            'assistant-used-model'
        ],
        score_columns = score_columns,
        effiency_columns = effiency_columns
    )

    summarizes['judge-assistant-format-report'] = judge_model_report(
        metrics_df = metrics_df,
        group_columns = [
            'judge-used-model', 
            'assistant-variant', 
            'assistant-format'
        ],
        score_columns = score_columns,
        effiency_columns = effiency_columns
    )
    
    summarizes['data-judge-variant-assistant-format-report'] = judge_model_report(
        metrics_df = metrics_df,
        group_columns = [
            'data-type', 
            'judge-used-model', 
            'assistant-variant',
            'assistant-used-model',
            'assistant-format'
        ],
        score_columns = score_columns,
        effiency_columns = effiency_columns
    )
    
    return summarizes

def judge_evalute_models(
    model_run_data: dict,
    target_keys: list,
    relevant_key_columns: dict,
    relevant_column_prefix: dict,
    summary_group_columns: list,
    summary_score_columns: list,
    summary_effiency_columns: list
):
    try:
        from ..misc.dict import get_dict_value
        from ..judge.utility import judge_summarize_models
        import pandas as pd
    except ImportError as e:
        raise ImportError("evaluation/use failed to import", e)
    
    metrics_rows = []
    for judge_name, judged in model_run_data.items():
        for judged_name, data in judged.items():
            for data_name, data_value in data.items():
                for record in data_value['records']:
                    row_data = {
                        'data-type': data_name
                    }

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
                                given_value = value
                                if 'question-type' == key:
                                    eval_split = value.split('-eval')
                                    variant_value = eval_split[0]
                                    format_value = eval_split[1].split('-judge')[0][1:]
                                    variant_column = f'{relevant_column_prefix[metric_key]}-variant'
                                    format_column = f'{relevant_column_prefix[metric_key]}-format'

                                    row_data[variant_column] = variant_value
                                    row_data[format_column] = format_value

                                    continue

                                row_data[value_column] = given_value
                    metrics_rows.append(row_data)
    
    collected_df = pd.DataFrame(metrics_rows)
    
    data_summaries = judge_summarize_models(
        metrics_df = collected_df,
        group_columns = summary_group_columns,
        score_columns = summary_score_columns,
        effiency_columns = summary_effiency_columns
    )
       
    return {
        'data': collected_df,
        'stats': data_summaries
    }
