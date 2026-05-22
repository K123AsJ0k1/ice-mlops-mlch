from airflow.sdk import DAG, task

with DAG(
    dag_id = "tutorial-hello-world", 
    start_date = None, 
    schedule = None,
    catchup = False,
    is_paused_upon_creation = False,
    tags = ["integration"]
) as dag:
    @task()
    def hello_world():
        print("airflow")

    hello_world()
