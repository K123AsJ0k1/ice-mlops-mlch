
def generator_produce_dataset(
    mlflow_client: any,
    dataset_ids: list,
    prompts: dict,
    experiment_id: str,
    trace_name: str,
    trace_attributes: dict,
    trace_tags: dict,
    dataset_limit: int,
    inference_parameters: dict,
    debug_prints: bool
):
    from ..generator.utility import generator_create_requests, generator_send_requests, generator_format_data

    generator_requests = generator_create_requests(
        mlflow_client = mlflow_client,
        dataset_ids = dataset_ids,
        prompts = prompts
    )
    
    generator_data = generator_send_requests(
        mlflow_client = mlflow_client,
        experiment_id = experiment_id,
        inference_requests = generator_requests,
        length_limit = trace_attributes['llm.n_ctx'],
        trace_name = trace_name,
        trace_attributes = trace_attributes,
        trace_tags = trace_tags,
        request_limit = dataset_limit,
        inference_parameters = inference_parameters,
        debug_prints = debug_prints
    )
    
    formatted_generator_data = generator_format_data(
        generator_data = generator_data,
        metric_columns = [
            'prompt-tokens',
            'completion-tokens',
            'total-tokens',
            'total-latency-sec',
            'prompt-processing-time-sec',
            'generation-time-sec',
            'input-tokens-per-sec',
            'output-tokens-per-sec',
            'time-to-first-token-sec',
            'tokens-per-second',
            'time-per-output-token-sec',
            'input-to-output-ratio',
            'context-window-utilization-pct',
            'characters',
            'user-prompt-length',
            'input-cost',
            'output-cost',
            'total-cost'
        ]
    )

    return formatted_generator_data