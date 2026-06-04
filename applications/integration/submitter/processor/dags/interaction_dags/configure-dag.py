from airflow.sdk import DAG, task

with DAG(
    dag_id = "submitter-configure-interaction", 
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
            from interaction_dags.sub_func.configure import configure_cloud_interaction
        except ImportError as e:
            raise ImportError("interaction-dags/configure failed to import", e)

        print('Configure cloud')
        # This is single target, the thing can be made multi target
        interaction_status = configure_cloud_interaction()

        return interaction_status
    
    task_result = configure_interaction()