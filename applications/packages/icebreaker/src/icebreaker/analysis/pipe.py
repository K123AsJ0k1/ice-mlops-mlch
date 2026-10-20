
def analysis_internal_pipe(
    swift_client: any,
    mlflow_client: any,
    experiment_name: str,
    run_name: str,
    run_tags: dict,
    run_parameters: dict,
    dataset_paths: list,
    storage_parameters: dict,
    group_columns: list,
    target_columns: list
):
    try:
        from ..analysis.use import analysis_internal_data_analysis
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
    
    formatted_internal_data = analysis_internal_data_analysis(
        swift_client = swift_client,
        run_parameters = run_parameters,
        dataset_paths = dataset_paths,
        storage_parameters = storage_parameters,
        group_columns = group_columns,
        target_columns = target_columns
    )
    
    for dataset_name in formatted_internal_data['metrics'].keys():
        parameters = formatted_internal_data['parameters']
        metrics = formatted_internal_data['metrics'][dataset_name]
        used_identity = dataset_name.split('formatted')[1][1:]
        
        mlflow_add_logs(
            mlflow_client = mlflow_client,
            run_id = run_id, 
            parameters = parameters,
            metrics = metrics,
            metrics_prefix = used_identity,
            metrics_step = 1,
            table = {},
            table_folder = '',
            table_name = ''
        )
        
    mlflow_end_run(
        mlflow_client = mlflow_client, 
        run_id = run_id, 
        status = 'FINISHED',
        end_time = None
    )
    
    return formatted_internal_data

def analysis_external_pipe(
    swift_client: any,
    mlflow_client: any,
    experiment_name: str,
    run_name: str,
    run_tags: dict,
    run_parameters: dict,
    dataset_paths: list,
    storage_parameters: dict,
    group_columns: list,
    target_columns: list
):
    try:
        from ..analysis.use import analysis_internal_data_analysis
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

    formatted_internal_data = {}

    for dataset_name in formatted_internal_data['metrics'].keys():
        parameters = formatted_internal_data['parameters']
        metrics = formatted_internal_data['metrics'][dataset_name]
        used_identity = dataset_name.split('formatted')[1][1:]
        
        mlflow_add_logs(
            mlflow_client = mlflow_client,
            run_id = run_id, 
            parameters = parameters,
            metrics = metrics,
            metrics_prefix = used_identity,
            metrics_step = 1,
            table = {},
            table_folder = '',
            table_name = ''
        )
        
    mlflow_end_run(
        mlflow_client = mlflow_client, 
        run_id = run_id, 
        status = 'FINISHED',
        end_time = None
    )
    
    return formatted_internal_data