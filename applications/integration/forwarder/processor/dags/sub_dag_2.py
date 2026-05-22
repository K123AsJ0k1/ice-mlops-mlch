from airflow.sdk import DAG, task, get_current_context

with DAG(
    dag_id = "tutorial-sub-2", 
    start_date = None, 
    schedule = None,
    catchup = False,
    is_paused_upon_creation = False,
    params = {
        "message": "none",
        "package": "none",
        "target": "none"
    },
    tags = ["integration"]
) as dag:
    @task()
    def sub_setup(
        params: str
    ):
        message = params['message'] + ' to sub-2'
        return message

    @task()
    def sub_preprocess(
        message: str
    ):
        airflow_context = get_current_context()
        message += ' that had ' +  airflow_context['params']['package']
        return message

    @task()
    def sub_utilizer(
        message: str
    ):
        airflow_context = get_current_context()
        message += ' to ' + airflow_context['params']['target']
        print(message)

    initial_message = sub_setup()
    partial_message = sub_preprocess(
        message = initial_message
    )
    sub_utilizer(
        message = partial_message
    )
