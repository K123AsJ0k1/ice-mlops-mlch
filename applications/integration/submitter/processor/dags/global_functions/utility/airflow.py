from airflow.hooks.base import BaseHook

def airflow_check_connection(
    connection_id: str
) -> bool:
    try:
        BaseHook.get_connection(connection_id)
        print('Connection ' + str(connection_id) + ' exists')
        return True
    except Exception as e:
        print('Connection ' + str(connection_id) + ' does not exist')
        return False