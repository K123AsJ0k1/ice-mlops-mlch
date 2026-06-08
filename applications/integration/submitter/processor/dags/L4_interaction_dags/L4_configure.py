from airflow.sdk import DAG, task

with DAG(
    dag_id = "submitter-configure-interaction", 
    start_date = None, 
    schedule = None,
    catchup = False,
    is_paused_upon_creation = False,
    params = {
        "swift-parameters": {},
        "storage-parameters": {},
        "process-parameters": {}
    },
    tags = [
        "integration",
        "configure",
        "interaction",
        "level-3"
    ] 
) as dag:
    @task()
    def configure_interaction(
        params: str
    ): 
        try:
            from L4_interaction_dags.tasks.configure_tasks import configure_task_cloud_interaction
        except ImportError as e:
            raise ImportError("interaction-dags/configure failed to import", e)
    
        interaction_status = configure_task_cloud_interaction(
            swift_parameters = params['swift-parameters'],
            storage_parameters = params['storage-parameters'],
            process_parameters = params['process-parameters'],
        )
        return interaction_status
    
    task_result = configure_interaction()