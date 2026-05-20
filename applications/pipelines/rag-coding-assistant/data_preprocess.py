from kfp import dsl

@dsl.component(
    base_image = "python:3.12.3",
    packages_to_install = []
)
def rag_dataset_processing(
    storage_parameters: dict,
    integration_parameters: dict
):
    print('RAG dataset processing test')

@dsl.component(
    base_image = "python:3.12.3",
    packages_to_install = []
)
def evaluation_dataset_processing(
    storage_parameters: dict,
    integration_parameters: dict
):
    print('Evaluation dataset processing test')

@dsl.component(
    base_image = "python:3.12.3",
    packages_to_install = []
)
def validation_dataset_processing(
    storage_parameters: dict,
    integration_parameters: dict
):
    print('Validation dataset processing test')

@dsl.pipeline(
    name = "preprocess-pipeline",
    description = "RAG, evalution and validation dataset processing"
)
def data_preprocess_pipeline(
    storage_parameters: dict,
    integration_parameters: dict
):
    task_1 = rag_dataset_processing(
        storage_parameters = storage_parameters,
        integration_parameters = integration_parameters
    )

    task_2 = evaluation_dataset_processing(
        storage_parameters = storage_parameters,
        integration_parameters = integration_parameters
    ).after(task_1)

    task_3 = validation_dataset_processing(
        storage_parameters = storage_parameters,
        integration_parameters = integration_parameters
    ).after(task_2)