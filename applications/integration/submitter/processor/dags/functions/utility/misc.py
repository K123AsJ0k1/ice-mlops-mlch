from airflow.hooks.base import BaseHook

def ssh_run_command(
    client: any,
    command: str
) -> any:
    stdin, stdout, stdeer = client.exec_command(command)
    formatted_print = stdout.read().decode('utf-8')
    formatted_error = stdeer.read().decode('utf-8')
    print('Error')
    print(formatted_error)
    return formatted_print

def base_check_connection(
    connection_id: str
) -> bool:
    try:
        BaseHook.get_connection(connection_id)
        print('Connection ' + str(connection_id) + ' exists')
        return True
    except Exception as e:
        print('Connection ' + str(connection_id) + ' does not exist')
        return False