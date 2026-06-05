
# Check imports and function
def bridge_ssh_interface(
    target_platform: str,
    interface_command: any
) -> any:
    try:
        from icebreaker.ssh.use import ssh_create_command
        from airflow.providers.ssh.operators.ssh import SSHHook
    except ImportError as e:
        raise ImportError("global_func//observability failed to import", e)

    print('Using SSH interface')
    interface_output = None
    if 0 < len(interface_command):
        ssh_command = ssh_create_command(
            commands = interface_command
        )
        print('Given string command: ' + str(ssh_command))
        if 0 < len(ssh_command):
            print('Creating SSH Hook for ' + str(target_platform))
            ssh_hook = SSHHook(
                ssh_conn_id = target_platform
            )
            
            print('Creating SSH connection')
            ssh_client = ssh_hook.get_conn()

            print('Running command')
            stdin, stdout, stdeer = ssh_client.exec_command(ssh_command)
            formatted_print = stdout.read().decode('utf-8')
            formatted_error = stdeer.read().decode('utf-8')

            if 0 < len(formatted_print):
                interface_output = formatted_print
            else:
                interface_output = formatted_error

            print('Closing SSH connection')
            ssh_client.close()
    return interface_output
# Check imports and function
def bridge_sftp_interface(
    target_platform: str,
    interface_command: any
) -> any:
    try:
        from airflow.providers.sftp.hooks.sftp import SFTPHook
    except ImportError as e:
        raise ImportError("interaction-dags/sub_func/observability failed to import", e)

    print('Using SFTP interface')
    interface_output = None
    print('Given command: ' + str(interface_command))
    if 0 < len(interface_command):
        print('Creating SFTP Hook for ' + str(target_platform))
        sftp_hook = SFTPHook(
            ssh_conn_id = target_platform
        )

        if interface_command[0] == 'list-directory':
            interface_output = sftp_hook.list_directory(
                path = interface_command[1]
            )
        if interface_command[0] == 'store-file':
            sftp_hook.store_file(
                remote_full_path = interface_command[1],
                local_full_path = interface_command[2]
            )
            interface_output = True
        if interface_command[0] == 'retrieve-file':
            sftp_hook.retrieve_file(
                remote_full_path = interface_command[1],
                local_full_path = interface_command[2]
            )
            interface_output = True
    return interface_output
# Check imports and function
def bridge_interface_interaction(
    storage_parameters: any,
    lock_location: str,
    interaction_parameters: any
) -> any:
    try:
        from icebreaker.interactions.concurrency import concurrency_get_client, concurrency_check_lock, concurrency_get_lock, concurrency_release_lock
    except ImportError as e:
        raise ImportError("interaction-dags/sub_func/observability failed to import", e)

    print('Platform interface interaction')
    interface_output = None
    lock_parameters = storage_parameters['lock'][lock_location]
    target_platform = interaction_parameters['platform']
    interaction_interface = interaction_parameters['interface']
    interface_command = interaction_parameters['command']

    lock_client = concurrency_get_client(
        lock_parameters = lock_parameters
    )

    lock_parameters['group'] = target_platform
    lock_parameters['resource'] = interaction_interface

    lock_active, lock_name = concurrency_check_lock(
        lock_parameters = lock_parameters,
        lock_client = lock_client
    )

    if not lock_active:
        lock_created, client_lock = concurrency_get_lock(
            lock_client = lock_client,
            lock_name = lock_name
        )

        if lock_created:
            try:
                if interaction_interface == 'ssh':
                    interface_output = bridge_ssh_interface(
                        target_platform = target_platform,
                        interface_command = interface_command
                    )
                if interaction_interface == 'sftp': 
                    interface_output = bridge_sftp_interface(
                        target_platform = target_platform,
                        interface_command = interface_command
                    )
            except Exception as e:
                print('Platform interface interaction error: ' + str(e))
            lock_released = concurrency_release_lock(
                lock_client = lock_client,
                client_lock = client_lock
            )
    return interface_output
