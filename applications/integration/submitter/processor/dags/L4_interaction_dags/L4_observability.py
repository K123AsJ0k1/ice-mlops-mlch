from airflow.sdk import DAG, task
  
with DAG(
    dag_id = "submitter-observability-interaction", 
    start_date = None, 
    schedule = None,
    catchup = False,
    is_paused_upon_creation = False,
    params = {
        "swift-parameters": {},
        "bucket-parameters": {},
        "storage-parameters": {}
    },
    tags = [
        "integration",
        "observability",
        "interaction",
        "level-4"
    ]
) as dag: 
    @task()
    def observability_interaction(
        params: any
    ):
        try:
            from L4_interaction_dags.tasks.observability_tasks import observability_task_submitter_interaction
        except ImportError as e:
            raise ImportError("interaction-dags/observability failed to import", e)

        interaction_status = observability_task_submitter_interaction(
            swift_parameters = params['swift-parameters'],
            bucket_parameters = params['bucket-parameters'],
            storage_parameters = params['storage-parameters']
        )
        return interaction_status

    task_result = observability_interaction()