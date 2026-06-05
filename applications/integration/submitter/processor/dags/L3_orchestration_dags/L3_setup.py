from airflow.sdk import DAG, task
 
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
# Should be okay 
with DAG(
    dag_id = "submitter-setup-orchestration", 
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
        "orchestration",
        "level-3"
    ] 
) as dag:
    @task()
    def setup_orchestration(
        params: any
    ):
        try:
            from orchestration_dags.local_func.setup import setup_platform_interaction
        except ImportError as e:
            raise ImportError("L3_orchestration_dags/L3_setup failed to import", e)

        expand_inputs = setup_platform_interaction(
            swift_parameters = params['swift-parameters'],
            bucket_parameters = params['bucket-parameters'],
            storage_parameters = params['storage-parameters'],
            platfrom_parameters = params['platform-parameters']
        )
        print('Storing ' + str(len(expand_inputs)) + ' objects')
        return expand_inputs

    storage_kwargs = setup_orchestration() 

    trigger_dags = TriggerDagRunOperator.partial(
        task_id = 'submitter_storage_interaction',
        wait_for_completion = False,
        reset_dag_run = False
    ).expand_kwargs(storage_kwargs)

    storage_kwargs >> trigger_dags