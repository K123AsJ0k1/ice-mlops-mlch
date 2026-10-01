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
        # Doesn't filter for some reason
        if not isinstance(val, list) or not isinstance(val, dict):
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

def mlflow_create_trace(
    mlflow_client: any,  
    trace_name: str,
    experiment_id: str,
    trace_attributes: dict,
    trace_tags: dict
) -> any:
    return mlflow_client.start_trace(
        name = trace_name, 
        attributes = trace_attributes, 
        tags = trace_tags, 
        experiment_id = experiment_id
    )

def mlflow_start_span(
    mlflow_client: any, 
    span_name: str,
    trace_id: any,
    span_id: any,
):
    return mlflow_client.start_span(
        name = span_name,
        trace_id = trace_id,
        parent_id = span_id
    )
    
def mlflow_end_span(
    mlflow_client: any,
    child_trace_id: any,
    child_span_id: any
):
    mlflow_client.end_span(
        trace_id = child_trace_id,
        span_id = child_span_id,
        status = "OK"
    )

def mlflow_end_trace(
    mlflow_client: any,
    trace_id: any
):
    mlflow_client.end_trace(
        trace_id = trace_id,
        status = "OK"
    )

def mlflow_register_prompts(
    mlflow_client: any,
    prompt_yaml: dict
):
    prompts = []
    for variant_name, variant_data in prompt_yaml.items(): 
        prompt_template = []
        for role, content in variant_data['messages'].items():
            prompt_template.append({
                'role': role,
                'content': content
            })
        
        for model_name, model_config in variant_data['models'].items():
            prompts.append({
                'name': variant_name + '-' + model_name,
                'config': model_config,
                'template': prompt_template
            })
    
    for prompt in prompts:
        mlflow_client.register_prompt(
            name = prompt['name'],
            template = prompt['template'],
            commit_message = 'Initial prompt',
            model_config = prompt['config']
        )

def mlflow_get_prompt(
    mlflow_client: any,
    prompt_name: str,
    prompt_version: int,
    prompt_replacements: dict
) -> any:
    fetched_template = mlflow_client.load_prompt(name_or_uri = prompt_name, version = prompt_version)
    
    prompt_details = {
        'prompt': fetched_template.format(**prompt_replacements),
        'config': fetched_template.model_config
    }

    return prompt_details

'''
def mlflow_create_span(
    mlflow_client: any, 
    span_name: str,
    trace_id: any,
    span_id: any,
    span_inputs: dict,
    span_attributes: dict,
    span_outputs: dict
):
    child_span = mlflow_client.start_span(
        name = span_name,
        trace_id = trace_id,
        parent_id = span_id
    )

    child_span.set_inputs(span_inputs)
    child_span.set_attributes(span_attributes)
    child_span.set_outputs(span_outputs)

    mlflow_client.end_span(
        trace_id = child_span.trace_id,
        span_id = child_span.span_id,
        status = "OK"
    )
'''
    


# consider synthetic dataset function
# consider llm as a judge function
# consider evalution function