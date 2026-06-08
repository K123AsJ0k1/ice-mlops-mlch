# check imports and function inputs
def airflow_check_connection(
    connection_id: str
) -> bool:
    try:
        from airflow.hooks.base import BaseHook
    except ImportError as e:
        raise ImportError("functions/utility/airflow failed to import", e) 

    try:
        BaseHook.get_connection(connection_id)
        print('Connection ' + str(connection_id) + ' exists')
        return True
    except Exception as e:
        print('Connection ' + str(connection_id) + ' does not exist')
        return False