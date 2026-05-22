from airflow.sdk import DAG, task, get_current_context

from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator

from functions.general import set_formatted_user

with DAG(
    dag_id = "tutorial-main", 
    start_date = None, 
    schedule = None,
    catchup = False,
    is_paused_upon_creation = False,
    params = {
        "token": "test",
        "user": "user@example.com",
        "message": "hello",
        "target": "airflow"
    },
    tags = ['integration']
) as dag:
    @task()
    def main_setup(
        params: str
    ):
        formatted_user = set_formatted_user(
            user = params['user']
        )
        message = formatted_user + ' used ' + params['token']
        return message

    @task()
    def main_preprocess(
        message: str
    ):
        airflow_context = get_current_context()
        message += ' and said ' +  airflow_context['params']['message']
        return message

    @task()
    def main_utilizer(
        message: str
    ):
        airflow_context = get_current_context()
        message += ' to ' + airflow_context['params']['target']
        print(message)

    initial_message = main_setup()
    partial_message = main_preprocess(
        message = initial_message
    )
    main_utilizer(
        message = partial_message
    )

    sub_1 = TriggerDagRunOperator(
        task_id = 'trigger_sub_1',
        trigger_dag_id = 'tutorial-sub-1', 
        conf = {
            'message': partial_message,
            'package': 'object',
            'target': 'Allas'
        },
        wait_for_completion = False,
        poke_interval = 20,
        reset_dag_run = True
    )

    sub_2 = TriggerDagRunOperator(
        task_id = 'trigger_sub_2',
        trigger_dag_id = 'tutorial-sub-2', 
        conf = {
            'message': partial_message,
            'package': 'job',
            'target': 'LUMI'
        },
        wait_for_completion = False,
        poke_interval = 20,
        reset_dag_run = True
    )

    sub_3 = TriggerDagRunOperator(
        task_id = 'trigger_sub_3',
        trigger_dag_id = 'tutorial-sub-3', 
        conf = {
            'message': partial_message,
            'package': 'Ray',
            'target': 'CPouta'
        },
        wait_for_completion = False,
        poke_interval = 20,
        reset_dag_run = True
    )

    initial_message >> partial_message >> sub_1 >> sub_2 >> sub_3
