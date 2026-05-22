
from airflow.sdk import DAG, task, get_current_context

from functions.general import set_formatted_user

with DAG(
    dag_id = "tutorial-dependency", 
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
    tags = ["integration"]
) as dag:
    @task()
    def setup(
        params: dict
    ):
        formatted_user = set_formatted_user(
            user = params['user']
        )
        message = formatted_user + ' used ' + params['token']
        return message

    @task()
    def preprocess(
        message: str
    ):
        airflow_context = get_current_context()
        message += ' and said ' +  airflow_context['params']['message']
        return message

    @task()
    def utilizer(
        message: str
    ):
        airflow_context = get_current_context()
        message += ' to ' + airflow_context['params']['target']
        print(message)

    initial_message = setup()
    partial_message = preprocess(
        message = initial_message
    )
    utilizer(
        message = partial_message
    )
