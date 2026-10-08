def evalution_rag_pipe(
    swift_client: any,
    qdrant_client: any,
    mlflow_client: any,
    experiment_name: str,
    run_name: str,
    run_tags: dict,
    storage_parameters: dict,
    collection_name: str,
    relevance_threshold: float,
    query_type: str,
    query_limit: int,
    query_column: str,
    weight_column: str,
    fusion_limit: int,
    dataset_paths: list,
    dense_model: any,
    dense_model_name: str,
    sparse_model: any,
    sparse_model_name: str,
    batch_size: int, 
    debug_prints: bool
) -> dict:
    try:
        from ..rag.use import rag_evalute_retrieval
        from ..mlflow.use import mlflow_get_or_create_experiment, mlflow_start_run, mlflow_add_logs, mlflow_end_run
    except ImportError as e:
        raise ImportError("evaluation/pipe failed to import", e)
    
    experiment_id = mlflow_get_or_create_experiment(
        mlflow_client = mlflow_client,
        name = experiment_name
    ) 

    run_id = mlflow_start_run(
        mlflow_client = mlflow_client,
        experiment_id = experiment_id, 
        run_name = run_name, 
        tags = run_tags
    ) 

    formatted_rag_data = rag_evalute_retrieval(
        swift_client = swift_client,
        qdrant_client = qdrant_client,
        storage_parameters = storage_parameters,
        collection_name = collection_name,
        relevance_threshold = relevance_threshold,
        query_type = query_type,
        query_limit = query_limit,
        query_column = query_column,
        weight_column = weight_column,
        fusion_limit = fusion_limit,
        dataset_paths = dataset_paths,
        dense_model = dense_model,
        dense_model_name = dense_model_name,
        sparse_model = sparse_model,
        sparse_model_name = sparse_model_name,
        batch_size = batch_size, 
        debug_prints = debug_prints
    )

    for dataset_name in formatted_rag_data['tables'].keys():
        parameters = formatted_rag_data['parameters']
        metrics = formatted_rag_data['metrics'][dataset_name]
        table = formatted_rag_data['tables'][dataset_name]
        used_identity = dataset_name.split('formatted')[1][1:]
        
        mlflow_add_logs(
            mlflow_client = mlflow_client,
            run_id = run_id, 
            parameters = parameters,
            metrics = metrics,
            metrics_prefix = used_identity,
            metrics_step = 1,
            table = table,
            table_folder = used_identity,
            table_name = 'ideal_rag_QA'
        )

    mlflow_end_run(
        mlflow_client = mlflow_client, 
        run_id = run_id, 
        status = 'FINISHED',
        end_time = None
    )

    return formatted_rag_data

def evalution_generator_pipe(
    mlflow_client: any,
    experiment_name: str,
    run_name: str,
    run_tags: dict,
    dataset_ids: list,
    prompts: dict,
    trace_name: str,
    trace_attributes: dict,
    trace_tags: dict,
    dataset_limit: int,
    inference_parameters: dict,
    debug_prints: bool
):
    try:
        from ..generator.use import generator_produce_dataset
        from ..mlflow.use import mlflow_get_or_create_experiment, mlflow_start_run, mlflow_add_logs, mlflow_end_run
    except ImportError as e:
        raise ImportError("evaluation/pipe failed to import", e)
    
    experiment_id = mlflow_get_or_create_experiment(
        mlflow_client = mlflow_client,
        name = experiment_name
    ) 

    run_id = mlflow_start_run(
        mlflow_client = mlflow_client,
        experiment_id = experiment_id, 
        run_name = run_name, 
        tags = run_tags
    ) 

    formatted_generator_dataset = generator_produce_dataset(
        mlflow_client = mlflow_client,
        dataset_ids = dataset_ids,
        prompts = prompts,
        experiment_id = experiment_id,
        trace_name = trace_name,
        trace_attributes = trace_attributes,
        trace_tags = trace_tags,
        dataset_limit = dataset_limit,
        inference_parameters = inference_parameters,
        debug_prints = debug_prints
    )

    parameters = formatted_generator_dataset['parameters']
    metrics = formatted_generator_dataset['metrics']
    table = formatted_generator_dataset['tables']
   
    mlflow_add_logs(
        mlflow_client = mlflow_client,
        run_id = run_id, 
        parameters = parameters,
        metrics = metrics,
        metrics_prefix = 'generator',
        metrics_step = 1,
        table = table,
        table_folder = 'generator',
        table_name = 'synthetic_QA_dataset'
    )

    mlflow_end_run(
        mlflow_client = mlflow_client, 
        run_id = run_id, 
        status = 'FINISHED',
        end_time = None
    )

    return formatted_generator_dataset