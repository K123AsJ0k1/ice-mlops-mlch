from airflow.sdk import DAG, task

from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
# Should be okay, but check trigger_dag_id and parameters
with DAG(
    dag_id = "submitter-operating-sequence", 
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
        "operating",
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

    fill_sub_dag = TriggerDagRunOperator(
        task_id = 'submitter_fill_orchestration',
        trigger_dag_id = 'submitter-fill-orchestration', 
        conf = parameters,
        wait_for_completion = True,
        poke_interval = 20,
        reset_dag_run = False
    )

    setup_sub_dag = TriggerDagRunOperator(
        task_id = 'submitter_setup_orchestration',
        trigger_dag_id = 'submitter-setup-orchestration', 
        conf = parameters,
        wait_for_completion = True,
        poke_interval = 20,
        reset_dag_run = False
    )
    
    run_sub_dag = TriggerDagRunOperator(
        task_id = 'submitter_run_orchestration',
        trigger_dag_id = 'submitter-run-orchestration', 
        conf = parameters,
        wait_for_completion = True,
        poke_interval = 20,
        reset_dag_run = False
    )

    parameters >> fill_sub_dag >> setup_sub_dag >> run_sub_dag