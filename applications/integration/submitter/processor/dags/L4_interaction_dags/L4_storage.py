from airflow.sdk import DAG, task

with DAG(
    dag_id = "submitter-storage-interaction", 
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
        "storage",
        "interaction",
        "level-3"
    ] 
) as dag:  
    @task() 
    def storage_interaction(
        params: any
    ):
        try: 
            from L4_interaction_dags.tasks.storage_tasks import storage_task_object_interaction
        except ImportError as e:
            raise ImportError("interaction-dags/storage failed to import", e)
        
        interaction_status = storage_task_object_interaction(
            swift_parameters = params['swift-parameters'],
            bucket_parameters = params['bucket-parameters'],
            storage_parameters = params['storage-parameters']
        )
        return interaction_status
    
    task_result = storage_interaction()