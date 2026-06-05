from airflow.sdk import DAG, task

from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
# Should be okay, but check parameters
with DAG(
    dag_id = "submitter-monitoring-trigger", 
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
        "platforms",
        "monitoring",
        "trigger",
        "level-1"
    ] 
) as dag: 
    @task()
    def monitor_platforms(
        params: str
    ): 
        try:
            from L1_trigger_dags.tasks.object_tasks import object_task_get_monitored
        except ImportError as e:
            raise ImportError("L1_trigger_dags/L1_monitoring failed to import", e)

        expand_inputs = object_task_get_monitored(
            swift_parameters = params['swift-parameters'],
            bucket_parameters = params['bucket-parameters'],
            storage_parameters = params['storage-parameters'],
            process_parameters = params['process-parameters']
        )
        
        print('Monitoring ' + str(len(expand_inputs)) + ' platforms')
        return expand_inputs 
    
    platform_kwargs = monitor_platforms()
    
    trigger_dags = TriggerDagRunOperator.partial(
        task_id = 'submitter_checking_sequences',
        wait_for_completion = False,
        reset_dag_run = False
    ).expand_kwargs(platform_kwargs)

    platform_kwargs >> trigger_dags