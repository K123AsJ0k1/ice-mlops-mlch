from airflow.sdk import DAG, task

from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
# Should be okay, but check trigger_dag_id and parameters
with DAG( 
    dag_id = "submitter-checking-sequence", 
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
        "checking",
        "sequence",
        "level-2"
    ]
) as dag: 
    @task()
    def get_sequence_parameters(
        params: str
    ):   
        platform = params['platform-parameters']['name']
        print('Running interactions in:' + str(platform))
        return params
     
    parameters = get_sequence_parameters()

    check_sub_dag = TriggerDagRunOperator(
        task_id = 'submitter_check_operation',
        trigger_dag_id = 'submitter-check-operation', 
        conf = parameters,
        wait_for_completion = True,
        poke_interval = 20,
        reset_dag_run = False
    )

    collect_sub_dag = TriggerDagRunOperator(
        task_id = 'submitter_collect_operation',
        trigger_dag_id = 'submitter-collect-operation', 
        conf = parameters,
        wait_for_completion = True,
        poke_interval = 20,
        reset_dag_run = False
    )

    parameters >> check_sub_dag >> collect_sub_dag