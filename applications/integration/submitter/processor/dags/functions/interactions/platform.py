from airflow.providers.ssh.operators.ssh import SSHHook
from airflow.providers.sftp.hooks.sftp import SFTPHook
 
from functions.interface.ssh import ssh_create_command, ssh_check_command
from functions.utility.misc import ssh_run_command

from functions.locking import concurrency_get_client, concurrency_check_lock, concurrency_get_lock, concurrency_release_lock
# Works 
def platform_ssh_interface(
    target_platform: str,
    interface_command: any
) -> any:
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
            interface_output = ssh_run_command(
                client = ssh_client,
                command = ssh_command
            )

            print('Closing SSH connection')
            ssh_client.close()
    return interface_output
# Works
def platform_sftp_interface(
    target_platform: str,
    interface_command: any
) -> any:
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
# Works
def platform_interface_interaction(
    storage_parameters: any,
    lock_location: str,
    interaction_parameters: any
) -> any:
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
                    interface_output = platform_ssh_interface(
                        target_platform = target_platform,
                        interface_command = interface_command
                    )
                if interaction_interface == 'sftp': 
                    interface_output = platform_sftp_interface(
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
