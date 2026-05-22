from airflow.sdk import DAG, task

from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator

from functions.interactions.objects import objects_get_operated
  
with DAG(
    dag_id = "submitter-operating-trigger", 
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
        "operating",
        "trigger",
        "level-0"
    ] 
) as dag:
    @task()
    def operate_platforms(
        params: str
    ): 
        expand_inputs = objects_get_operated(
            swift_parameters = params['swift-parameters'],
            bucket_parameters = params['bucket-parameters'],
            storage_parameters = params['storage-parameters'],
            process_parameters = params['process-parameters'],
        )
        
        print('Operating ' + str(len(expand_inputs)) + ' platforms')
        return expand_inputs
    
    platform_kwargs = operate_platforms()
    
    trigger_dags = TriggerDagRunOperator.partial(
        task_id = 'submitter_interaction_sequences',
        wait_for_completion = False,
        reset_dag_run = False
    ).expand_kwargs(platform_kwargs)

    platform_kwargs >> trigger_dags
    