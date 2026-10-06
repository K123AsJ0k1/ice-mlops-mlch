
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

def evalution_ranking_metrics(
    retrieved_ids: list, 
    true_relevant_weights: dict,
    relevance_threshold: float = 2.0  
):
    # Threshold: Grades >= 2 count as binary "relevant"
    """
    Computes standard academic retrieval metrics.
    - P@1 & R@3 use binary binarization (Grade >= rel_threshold).
    - NDCG@3 & NDCG@5 use full graded relevance (3, 2, 1, 0).
    """
    try: 
        import numpy as np
    except ImportError as e:
        raise ImportError("qdrant/utility failed to import", e)

    # 1. Binary relevance vector for P@1 and R@3 (Grade >= 2)
    binary_relevance = [
        1 if true_relevant_weights.get(_id, 0) >= relevance_threshold else 0 
        for _id in retrieved_ids
    ]
    
    total_relevant_docs = sum(
        1 for weight in true_relevant_weights.values() if weight >= relevance_threshold
    )

    # --- Precision@1 (Binary) ---
    p_at_1 = float(binary_relevance[0]) if binary_relevance else 0.0

    # --- Recall@3 (Binary) ---
    if total_relevant_docs > 0:
        hits_top_3 = sum(binary_relevance[:3])
        r_at_3 = float(hits_top_3 / total_relevant_docs)
    else:
        r_at_3 = 0.0

    # --- Reciprocal Rank (RR / MRR single query) ---
    rr = 0.0
    for rank_idx, rel in enumerate(binary_relevance, start=1):
        if rel == 1:
            rr = 1.0 / rank_idx
            break

    # --- Average Precision (AP / MAP single query) ---
    if total_relevant_docs > 0:
        running_hits = 0
        precision_sum = 0.0
        
        for rank_idx, rel in enumerate(binary_relevance, start=1):
            if rel == 1:
                running_hits += 1
                precision_at_k = running_hits / rank_idx
                precision_sum += precision_at_k
                
        ap = float(precision_sum / total_relevant_docs)
    else:
        ap = 0.0

    # 2. Full Graded relevance vector for NDCG (Supports 3, 2, 1, 0)
    graded_relevance = [true_relevant_weights.get(_id, 0) for _id in retrieved_ids]

    def compute_graded_dcg(rel_vector):
        return sum([((2**r) - 1) / np.log2(idx + 2) for idx, r in enumerate(rel_vector)])
    
    def compute_graded_idcg(k):
        sorted_weights = sorted(true_relevant_weights.values(), reverse=True)
        ideal_relevance = (sorted_weights + [0] * k)[:k]
        return compute_graded_dcg(ideal_relevance)

    # Compute Actual & Ideal DCG
    dcg_3 = compute_graded_dcg(graded_relevance[:3])
    dcg_5 = compute_graded_dcg(graded_relevance[:5])
    
    idcg_3 = compute_graded_idcg(3)
    idcg_5 = compute_graded_idcg(5)
    
    # Compute NDCG
    ndcg_3 = float(dcg_3 / idcg_3) if idcg_3 > 0 else 0.0
    ndcg_5 = float(dcg_5 / idcg_5) if idcg_5 > 0 else 0.0
    
    return {
        'p@1': p_at_1,
        'r@3': r_at_3,
        'rr': rr,
        'ap': ap,
        'ndcg@3': ndcg_3,
        'ndcg@5': ndcg_5
    }

def evaluation_get_statistics(
    gathered_metrics: dict,
    percentile_filter: list
):
    try:
        import statistics
        import numpy as np
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)
    
    summary_statistics = {}
    for key, value in gathered_metrics.items():
        key_mean_column = f'{key}-mean'
        key_median_column = f'{key}-median'
        key_mean = statistics.mean(value)
        key_median = statistics.median(value)
        summary_statistics[key_mean_column] = float(key_mean)
        summary_statistics[key_median_column] = float(key_median)

        if not key in percentile_filter:
            key_p95_column = f'{key}-p95'
            key_p99_column = f'{key}-p99'
            key_p95 = np.percentile(value, 95)
            key_p99 = np.percentile(value, 99)
            summary_statistics[key_p95_column] = float(key_p95)
            summary_statistics[key_p99_column] = float(key_p99)
    return summary_statistics

def evalution_rag_report(
    metrics_df: any,
    group_columns: list,
    target_columns: list
):
    try:
        import numpy as np
        import pandas as pd
    except ImportError as e:
        raise ImportError("evaluation/use failed to import", e)

    def p95(x): 
        clean_x = x.dropna()
        return np.percentile(clean_x, 95) if len(clean_x) > 0 else np.nan
    def p99(x): 
        clean_x = x.dropna()
        return np.percentile(clean_x, 99) if len(clean_x) > 0 else np.nan
    
    summary_table = metrics_df.groupby(group_columns)[target_columns].agg(
        ['mean', 'std', 'median', p95, p99, 'min', 'max']
    )

    return summary_table.T

def evalution_summarize_rag(
    metrics_df: any,
    target_columns: list
):
    try:
        from ..judge.utility import judge_rag_report
    except ImportError as e:
        raise ImportError("evaluation/use failed to import", e)

    summarizes = {}

    summarizes['data-report'] = judge_rag_report(
        metrics_df = metrics_df,
        group_columns = [
            'data-type'
        ],
        target_columns = target_columns
    )

    return summarizes

def evalute_evalute_rag(
    rag_run_data: dict,
    relevant_columns: dict,
    summary_target_columns: list
):
    try:
        from ..judge.utility import judge_summarize_rag
        import pandas as pd
    except ImportError as e:
        raise ImportError("evaluation/use failed to import", e)
    
    metrics_rows = []
    for model_name, data in rag_run_data.items():
        for data_name, data_value in data.items():
            for case in data_value:
                row_data = {
                    'data-type': data_name
                }
                for key, value in case.items():
                    if key in relevant_columns:
                        row_data[key] = value
                metrics_rows.append(row_data)
                   
    collected_df = pd.DataFrame(metrics_rows)
    
    data_summaries = judge_summarize_rag(
        metrics_df = collected_df,
        target_columns = summary_target_columns
    )
      
    return {
        'data': collected_df,
        'stats': data_summaries
    }

def evalute_add_datasets(
    swift_client: any,
    mlflow_client: any,
    storage_parameters: any,
    experiment_name: str,
    dataset_type: str,
    dataset_paths: list,
    dataset_tags: dict
):
    try:
        from ..objects.use import objects_get_data
        from ..mlflow.use import mlflow_create_dataset, mlflow_get_or_create_experiment
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)

    experiment_id = mlflow_get_or_create_experiment(
        mlflow_client = mlflow_client,
        name = experiment_name
    ) 
    
    dataset_ids = []
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
        target_df = data_object[0]

        name_split = dataset_name.split('-')
        data_name = f'{name_split[0]}_{name_split[1]}'
        data_part = name_split[-1] 
        formatted_records = []
        if dataset_type == 'validation':
            for _, row in target_df.iterrows():
                if not row['chapter'] == 0:
                    formatted_records.append({
                        'inputs': {
                            'question': row['topic']
                        },
                        'expectations': {
                            'ground_truth': row['content'],
                            'relevance': row['relevance'],
                            'weights': row['ranking-weights']
                        },
                        'source': {
                            'source_type': 'HUMAN'
                        },
                        'tags': {
                            'name': data_name,
                            'part': data_part
                        }
                    })
        used_dataset_name = f'{data_name}_{dataset_type}_{data_part}' 
        dataset_id = mlflow_create_dataset(
            mlflow_client = mlflow_client,
            dataset_name = used_dataset_name,
            experiment_id = experiment_id,
            dataset_tags = dataset_tags,
            dataset_records = formatted_records
        )
        dataset_ids.append(dataset_id)
    return dataset_ids