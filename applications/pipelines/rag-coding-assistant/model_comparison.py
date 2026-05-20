from kfp import dsl

@dsl.component(
    base_image = "python:3.12.3",
    packages_to_install = []
)
def baseline_model_comparison(
    storage_parameters: dict,
    integration_parameters: dict
):
    print('Baseline comparison test')

@dsl.component(
    base_image = "python:3.12.3",
    packages_to_install = []
)
def pe_model_comparison(
    storage_parameters: dict,
    integration_parameters: dict
):
    print('PE comparsion test')

@dsl.component(
    base_image = "python:3.12.3",
    packages_to_install = []
)
def rag_model_comparison(
    storage_parameters: dict,
    integration_parameters: dict
):
    print('RAG comparison test')

@dsl.component(
    base_image = "python:3.12.3",
    packages_to_install = []
)
def bc_model_comparison(
    storage_parameters: dict,
    integration_parameters: dict
):
    print('BC comparison test')

@dsl.component(
    base_image = "python:3.12.3",
    packages_to_install = []
)
def pe_rag_bc_model_comparison(
    storage_parameters: dict,
    integration_parameters: dict
):
    print('PE-RAG-BC comparison test')

@dsl.pipeline(
    name = "model-comparison-pipeline",
    description = "Baseline, PE, RAG, BC and PE-RAG-BC model comparison"
)
def model_comparison_pipeline(
    storage_parameters: dict,
    integration_parameters: dict
):
    task_1 = baseline_model_comparison(
        storage_parameters = storage_parameters,
        integration_parameters = integration_parameters
    )

    task_2 = pe_model_comparison(
        storage_parameters = storage_parameters,
        integration_parameters = integration_parameters
    ).after(task_1)

    task_3 = rag_model_comparison(
        storage_parameters = storage_parameters,
        integration_parameters = integration_parameters
    ).after(task_2)

    task_4 = bc_model_comparison(
        storage_parameters = storage_parameters,
        integration_parameters = integration_parameters
    ).after(task_3)

    task_5 = pe_rag_bc_model_comparison(
        storage_parameters = storage_parameters,
        integration_parameters = integration_parameters
    ).after(task_4)