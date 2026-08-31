
def evaluation_summarize_metrics(
    list_of_dicts: list,
    relevant_columns: list,
    wanted_stats: list,
    group_column: str
) -> dict:
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("evaluation/use failed to import", e)
    
    """
    Computes overall and grouped statistical summaries for specified columns from a list of dicts.
    Flattens nested dict fields dynamically using json_normalize.
    """
    if not list_of_dicts:
        return {"general": {}, "grouped": {}}

    # 1. Flatten nested dictionaries (e.g., metadata.assistant_variant -> metadata.assistant_variant)
    df = pd.DataFrame(list_of_dicts)
    # 2. Filter for existing columns to avoid KeyErrors
    general_stats_df = df[relevant_columns].agg(wanted_stats)
    
    # Handle single vs multiple stats structure output
    if isinstance(general_stats_df, pd.Series):
        general_stats_dict = general_stats_df.to_dict()
    else:
        general_stats_dict = general_stats_df.to_dict()

    summarized_metrics = {
        'general': general_stats_dict,
    }

    # 4. Compute grouped metrics (if group_column specified and present)
    
    group_stats_df = df.groupby(group_column)[relevant_columns].agg(wanted_stats)
    
    # Unstack/flatten MultiIndex columns into nested dictionaries
    flattened_group_stats = {}
    
    # MultiIndex columns (col, stat)
    if isinstance(group_stats_df.columns, pd.MultiIndex):
        for (col, stat), group_series in group_stats_df.items():
            if col not in flattened_group_stats:
                flattened_group_stats[col] = {}
            flattened_group_stats[col][str(stat)] = group_series.to_dict()
    else:
        # Single stat provided
        stat_name = str(wanted_stats[0]) if len(wanted_stats) == 1 else "stat"
        for col, group_series in group_stats_df.items():
            flattened_group_stats[col] = {stat_name: group_series.to_dict()}

    group_key = f'{group_column}-group'
    summarized_metrics[group_key] = flattened_group_stats

    return summarized_metrics

def evaluation_summarize_list(
    list_of_values: list,
    column_name: str,
    wanted_stats: list
) -> dict:
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("evaluation/use failed to import", e)
    
    """
    Computes statistical summary metrics on a flat 1D list of values.
    """
    if not list_of_values:
        return {}

    series = pd.Series(list_of_values, name=column_name)
    stats_result = series.agg(wanted_stats)
    
    # Convert Pandas Series/Scalar back to native Python dict
    if isinstance(stats_result, pd.Series):
        return {str(k): (float(v) if pd.notnull(v) else None) for k, v in stats_result.to_dict().items()}
    return {str(wanted_stats[0]): float(stats_result)}

def evaluation_nested_metrics(
    run_data: list,
    root_keys: list,
    target_keys: list,
    relevant_key_columns: dict,
    wanted_stats: list,
    key_group_column: dict
) -> dict:
    try:
        from ..misc.dict import get_dict_value
    except ImportError as e:
        raise ImportError("evaluation/use failed to import", e)

    key_data = {}
    for root_key, value_type in root_keys.items():
        if not root_key in key_data:
            if not value_type == 'nested':
                key_data[root_key] = []

        root_data = run_data[root_key]
        
        if value_type == 'nested':
            for data in root_data:
                metadata = data['metadata']
                for target_key in target_keys:
                    sub_dict_key = target_key.split('|')[0]
                    if 0 < len(data[sub_dict_key]):
                        if not target_key in key_data:
                            key_data[target_key] = []
                        key_value = get_dict_value(
                            target_dict = data,
                            key_path = target_key,
                            separator = '|'
                        )
                        merged_data = key_value | metadata
                        key_data[target_key].append(merged_data)
        if value_type == 'list':
            key_data[root_key] = root_data
    
    gathered_stats = {}
    for target_key, target_data in key_data.items():
        case_relevant_columns = relevant_key_columns[target_key]
        gathered_stats[target_key] = evaluation_summarize_metrics(
            list_of_dicts = target_data,
            relevant_columns = case_relevant_columns,
            wanted_stats = wanted_stats,
            group_column = key_group_column[target_key]
        )
        
    return gathered_stats
