def assistant_produce_answers(
    target_df: any,
    assistant_prompts: dict,
    dataset_name: str,
    assistant_model: str,
    type_column: str,
    data_ratio: dict,
    join_prompts: bool,
    qdrant_client: any,
    query_type: str,
    collection_name: str,
    query_limit: int,
    fusion_limit: int,
    dense_model_name: str,
    dense_model: any,
    sparse_model_name: str,
    sparse_model: any,
    batch_size: int,
    relevance_threshold: float,
    char_to_token_ratio: float,
    length_limit: int,
    inference_parameters: any,
    controller_model: str,
    controller_prompts: dict,
    summary_root_keys: dict,
    summary_target_keys: list,
    summary_relevant_key_columns: dict,
    summary_wanted_stats: list,
    summary_key_group_column: dict
):
    try:
        from ..assistant.use import assistant_create_requests, assistant_generate_answers, assistant_print_answers
        from ..evaluation.use import evaluation_nested_metrics
    except ImportError as e:
        raise ImportError("assistant/use failed to import", e)

    assistant_requests = assistant_create_requests(
        target_df = target_df,
        prompt_parameters = assistant_prompts,
        dataset_name = dataset_name,
        target_model = assistant_model,
        type_column = type_column,
        data_ratio = data_ratio,
        join_prompts = join_prompts,
        qdrant_client = qdrant_client,
        query_type = query_type, 
        collection_name = collection_name,
        query_limit = query_limit,
        fusion_limit = fusion_limit,
        dense_model_name = dense_model_name,
        dense_model = dense_model,
        sparse_model_name = sparse_model_name,
        sparse_model = sparse_model,
        batch_size = batch_size,
        relevance_threshold = relevance_threshold
    )

    assistant_run_data = assistant_generate_answers(
        dataset_inference_requests = assistant_requests[0],
        char_to_token_ratio = char_to_token_ratio,
        length_limit = length_limit,
        inference_parameters = inference_parameters,
        controller_model = controller_model,
        controller_prompts = controller_prompts,
        debug_prints = False
    ) 

    try:
        assistant_print_answers(
            run_data = assistant_run_data
        )
    except Exception as e:
        print(e)

    assistant_run_data['rag-metrics'] = assistant_requests[1]

    try:
        nested_stats = evaluation_nested_metrics(
            run_data = assistant_run_data,
            root_keys = summary_root_keys,
            target_keys = summary_target_keys,
            relevant_key_columns = summary_relevant_key_columns,
            wanted_stats = summary_wanted_stats,
            key_group_column = summary_key_group_column
        )

        assistant_run_data['stats'] = assistant_run_data['stats'] | nested_stats
    except Exception as e:
        print(e)

    return assistant_run_data