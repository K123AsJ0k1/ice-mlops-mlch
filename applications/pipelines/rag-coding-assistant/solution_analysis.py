from kfp import dsl

@dsl.component(
    base_image = "python:3.12.3",
    packages_to_install = []
)
def model_selection(
    storage_parameters: dict,
    integration_parameters: dict
):
    print('Model selection test')

@dsl.component(
    base_image = "python:3.12.3",
    packages_to_install = []
)
def model_deployment(
    storage_parameters: dict,
    integration_parameters: dict
):
    print('Model deployment test')

@dsl.pipeline(
    name = "solution-analysis-pipeline",
    description = "Metrics based model selection and deployment"
)
def solution_analysis_pipeline(
    storage_parameters: dict,
    integration_parameters: dict
):
    task_1 = model_selection(
        storage_parameters = storage_parameters,
        integration_parameters = integration_parameters
    )

    task_2 = model_deployment(
        storage_parameters = storage_parameters,
        integration_parameters = integration_parameters
    ).after(task_1)