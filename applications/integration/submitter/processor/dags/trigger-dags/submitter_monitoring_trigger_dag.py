from airflow.sdk import DAG, task

from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator

from functions.interactions.objects import objects_get_monitored
  
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
        "level-0"
    ] 
) as dag:
    @task()
    def monitor_platforms(
        params: str
    ): 
        expand_inputs = objects_get_monitored(
            swift_parameters = params['swift-parameters'],
            bucket_parameters = params['bucket-parameters'],
            storage_parameters = params['storage-parameters'],
            process_parameters = params['process-parameters']
        )
        
        print('Monitoring ' + str(len(expand_inputs)) + ' platforms')
        return expand_inputs
    
    platform_kwargs = monitor_platforms()
    
    trigger_dags = TriggerDagRunOperator.partial(
        task_id = 'main_trigger_subdags',
        wait_for_completion = False,
        reset_dag_run = False
    ).expand_kwargs(platform_kwargs)

    platform_kwargs >> trigger_dags