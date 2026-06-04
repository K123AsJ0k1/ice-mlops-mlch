from airflow.sdk import DAG, task
 
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator

#from functions.interactions.setup import setup_platform_interaction

with DAG(
    dag_id = "submitter-setup-operation", 
    start_date = None, 
    schedule = None,
    catchup = False,
    is_paused_upon_creation = False,
    params = {
        "swift-parameters": {},
        "bucket-parameters": {},
        "storage-parameters": {},
        "platform-parameters": {}
    },
    tags = [
        "integration",
        "platforms",
        "setup",
        "operation",
        "level-2"
    ]
) as dag:
    @task()
    def operate_setup_interaction(
        params: any
    ):
        try:
            from functions.interactions.setup import setup_platform_interaction
        except ImportError as e:
            raise ImportError("orchestration-dags/setup failed to import", e)

        #platform = params['platform-parameters']['name']
        #print('Operating setup interaction in:' + str(platform))
        expand_inputs = setup_platform_interaction(
            swift_parameters = params['swift-parameters'],
            bucket_parameters = params['bucket-parameters'],
            storage_parameters = params['storage-parameters'],
            platfrom_parameters = params['platform-parameters']
        )
        print('Storing ' + str(len(expand_inputs)) + ' objects')
        return expand_inputs

    storage_kwargs = operate_setup_interaction()

    trigger_dags = TriggerDagRunOperator.partial(
        task_id = 'submitter_storage_interaction',
        wait_for_completion = False,
        reset_dag_run = False
    ).expand_kwargs(storage_kwargs)

    storage_kwargs >> trigger_dags