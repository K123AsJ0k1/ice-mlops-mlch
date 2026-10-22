
def analysis_internal_pipe(
    swift_client: any,
    mlflow_client: any,
    experiment_name: str,
    run_name: str,
    run_tags: dict,
    run_parameters: dict,
    dataset_paths: list,
    storage_parameters: dict
) -> dict: 
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
        storage_parameters = storage_parameters
    )
    
    for dataset_name in formatted_internal_data['metrics'].keys():
        parameters = formatted_internal_data['parameters']
        metrics = formatted_internal_data['metrics'][dataset_name]
        table = formatted_internal_data['tables'][dataset_name]
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
            table_name = 'internal_validation_material'
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
    dataset_defaults: dict,
    path_end_prefix: str
) -> dict:
    try:
        from ..analysis.use import analysis_external_data_analysis
        from ..objects.use import objects_store_data, objects_get_prefix_list
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
    
    formatted_internal_data = analysis_external_data_analysis(
        swift_client = swift_client,
        run_parameters = run_parameters,
        dataset_paths = dataset_paths,
        storage_parameters = storage_parameters,
        dataset_defaults = dataset_defaults
    )
    
    for dataset_name in formatted_internal_data['metrics'].keys():
        parameters = formatted_internal_data['parameters']
        metrics = formatted_internal_data['metrics'][dataset_name]
        used_identity = dataset_name.split('external')[1][1:]
        table = formatted_internal_data['tables'][dataset_name]

        artifact = {
            'parameters': parameters,
            'metrics': metrics
        }

        artifact_path_name = f'{dataset_name}-{path_end_prefix}-metrics-'

        artifact_list = objects_get_prefix_list(
            storage_client = swift_client,
            storage_parameters = storage_parameters,
            object_prefix = artifact_path_name
        )
        next_index = len(artifact_list) + 1

        artifact_path_name += f'{next_index}.pkl'
         
        storage_parameters['object-name'] = 'arti'
        storage_parameters['object-serialization'] = 'pickle'
        storage_parameters['path-replacers'] = {
            'name': 'METRICS'
        }
        storage_parameters['path-names'] = [
            artifact_path_name
        ]
        storage_parameters['debug-prints'] = True
        storage_parameters['lock-parameters'] = {}
        storage_parameters['lock-location'] = None
        storage_parameters['overwrite'] = True
        
        artifact_stored = objects_store_data(
            swift_client = swift_client,
            storage_parameters = storage_parameters,
            object_data = artifact,
            object_metadata = {}
        )
        
        table_path_name = f'{dataset_name}-{path_end_prefix}.parquet'
    
        storage_parameters['object-name'] = 'data'
        storage_parameters['object-serialization'] = 'parquet'
        storage_parameters['path-replacers'] = {
            'name': 'SOURCE'
        }
        storage_parameters['path-names'] = [
            table_path_name
        ]
        storage_parameters['debug-prints'] = True
        storage_parameters['lock-parameters'] = {}
        storage_parameters['lock-location'] = None
        storage_parameters['overwrite'] = True
        
        table_stored = objects_store_data(
            swift_client = swift_client,
            storage_parameters = storage_parameters,
            object_data = table,
            object_metadata = {}
        )
        
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