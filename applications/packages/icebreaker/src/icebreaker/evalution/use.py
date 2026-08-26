def evalution_summarize_metrics(
    list_of_dicts: list,
    relevant_columns: list,
    wanted_stats: list,
    group_column: str
):
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("evaluation/use failed to import", e)
    
    data_df = pd.DataFrame(list_of_dicts)

    general_stats_df = data_df[relevant_columns].agg(wanted_stats)

    group_stats_df = data_df.groupby(group_column)[relevant_columns].agg(wanted_stats)

    flattened_group_stats = {}
    for (metric, stat), category_values in group_stats_df.to_dict().items():
        if metric not in flattened_group_stats:
            flattened_group_stats[metric] = {}
        flattened_group_stats[metric][stat] = category_values

    group_key = f'{group_column}-group'

    summarized_metrics = {
        'general': general_stats_df.to_dict(),
        group_key: flattened_group_stats
    }

    return summarized_metrics 

def evalution_summarize_list(
    list_of_values: list,
    used_column: list,
    wanted_stats: list
):
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("evaluation/use failed to import", e)

    data_df = pd.DataFrame(list_of_values, columns = [used_column])

    general_stats_df = data_df[used_column].agg(wanted_stats)

    return general_stats_df.to_dict()

def evalution_nested_metrics(
    run_data: list,
    target_keys: list,
    relevant_key_columns: dict,
    wanted_stats: list,
    key_group_column: dict
):
    try:
        from ..misc.dict import get_dict_value
    except ImportError as e:
        raise ImportError("evaluation/use failed to import", e)

    gathered_stats = {}
    for target_key in target_keys:
        data = get_dict_value(
            target_dict = run_data,
            key_path = target_key,
            separator = '|'
        )
        
        key_stats = {}
        if 0 < len(data):
            if isinstance(data[0], dict):
                root_key = target_key.split('|')[0]
                key_stats = evalution_summarize_metrics(
                    list_of_dicts = data,
                    relevant_columns = relevant_key_columns[root_key],
                    wanted_stats = wanted_stats,
                    group_column = key_group_column[root_key]
                )
            else:
                root_key = target_key.split('|')[0]
                key_stats = evalution_summarize_list(
                    list_of_values = data,
                    used_column = root_key,
                    wanted_stats = wanted_stats
                )
                
        gathered_stats[target_key] = key_stats

    return gathered_stats
    
