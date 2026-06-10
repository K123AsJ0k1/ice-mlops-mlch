def mlflow_get_or_create_experiment(
    mlflow_client: any,
    name: str
) -> str:
    exp = mlflow_client.get_experiment_by_name(name)
    if exp is not None:
        return exp.experiment_id
    return mlflow_client.create_experiment(name=name)

def mlflow_start_run(
    mlflow_client: any,
    experiment_id: str, 
    run_name: str, 
    tags: any
) -> str:
    run = mlflow_client.create_run(
        experiment_id = experiment_id, 
        run_name = run_name,
        tags = tags
    )
    return run.info.run_id

def mlflow_get_run(
    mlflow_client: any,
    run_id: str,
) -> any:
    return mlflow_client.get_run(run_id)

def mlflow_log_metrics(
    mlflow_client: any,
    run_id: str, 
    metrics: any, 
    step: int
) -> None:
    for key, val in metrics.items():
        if not isinstance(val, list):
            mlflow_client.log_metric(
                run_id = run_id, 
                key = key, 
                value = val, 
                step = step
            )

def mlflow_log_artifact(
    mlflow_client: any,
    run_id: str, 
    local_path: str, 
    artifact_path: str
):
    mlflow_client.log_artifact(run_id, local_path, artifact_path)

def mlflow_log_model(
    run_id: str, 
    artifact_path: str, 
    registered_name: str = None
):
    with mlflow.start_run(run_id=run_id):
        mlflow.pyfunc.log_model(
            artifact_path = artifact_path,
            registered_model_name = registered_name
        )

def mlflow_change_run_status(
    mlflow_client: any, 
    run_id: str, 
    status: str
) -> None:
    sanitized_status = status.upper()

    valid_statuses = ["FINISHED", "FAILED", "KILLED", "RUNNING"]
    if sanitized_status in valid_statuses:
        mlflow_client.update_run(
            run_id = run_id, 
            status = sanitized_status
        )

# consider synthetic dataset function
# consider llm as a judge function
# consider evalution function