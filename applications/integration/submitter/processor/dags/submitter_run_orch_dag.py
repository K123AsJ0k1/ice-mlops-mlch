from airflow.sdk import DAG, task
 
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
  
from functions.interactions.run import run_platform_interaction

with DAG(
    dag_id = "submitter-run-operation", 
    start_date = None, 
    schedule = None,
    catchup = False,
    is_paused_upon_creation = False,
    max_active_runs = 1,
    params = {
        "swift-parameters": {},
        "bucket-parameters": {},
        "storage-parameters": {},
        "platform-parameters": {}
    },
    tags = [
        "integration",
        "platforms",
        "run",
        "operation",
        "level-2"
    ]
) as dag: 
    @task()
    def operate_run_interaction(
        params: any
    ):
        expand_inputs = run_platform_interaction(
            swift_parameters = params['swift-parameters'],
            bucket_parameters = params['bucket-parameters'],
            storage_parameters = params['storage-parameters'],
            platfrom_parameters = params['platform-parameters']
        )
        print('Storing ' + str(len(expand_inputs)) + ' objects')
        return expand_inputs

    storage_kwargs = operate_run_interaction()

    trigger_dags = TriggerDagRunOperator.partial(
        task_id = 'submitter_storage_interaction',
        wait_for_completion = False,
        reset_dag_run = False
    ).expand_kwargs(storage_kwargs)

    storage_kwargs >> trigger_dags