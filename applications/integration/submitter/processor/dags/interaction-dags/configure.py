from airflow.sdk import DAG, task
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator

with DAG(
    dag_id = "submitter-configure-cloud", 
    start_date = None, 
    schedule = None,
    catchup = False,
    is_paused_upon_creation = False,
    params = {
        "swift-parameters": {},
        "bucket-parameters": {},
        "storage-parameters": {},
        "process-parameters": {}
    },
    tags = [
        "integration",
        "storage",
        "interaction",
        "level-3"
    ] 
) as dag:
    @task()
    def configure_cloud(
        params: str
    ): 
        try:
            from functions.interactions.configuration import configuration_cloud_interaction
        except ImportError as e:
            raise ImportError("interaction-dags/configure failed to import", e)

        print('Configure cloud')
        # This is single target, the thing can be made multi target
        interaction_status = configuration_cloud_interaction()

        return interaction_status
    
    task_result = configure_cloud()