# Check imports and confirm function
def setup_venv_check(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    commands: any,
    configs: any
) -> bool:
    try: 
        from icebreaker.linux.use import linux_open_directory
        from icebreaker.linux.utility import linux_format_list
        from icebreaker.misc.general import fill_list_values
        from functions.interactions.bridge import bridge_ssh_interface
    except ImportError as e:
        raise ImportError("L3_orchestration_dags/actions/setup_actions failed to import", e)

    print('Running venv check')
    
    venv_exists = False
    venv_name = configs['venv']['name']
    venv_folder = configs['venv']['path']

    directory_command = linux_open_directory(
        path = venv_folder
    )
    
    check_venv_command = fill_list_values(
        target = commands['venv-check'],
        values = [
            directory_command
        ]
    )
    
    interaction_output = bridge_ssh_interface(
        storage_parameters = storage_parameters,
        lock_location = lock_location,
        interaction_parameters = {
            'platform': target_platform,
            'interface': 'ssh',
            'command': check_venv_command
        }
    )
    
    folders, files = linux_format_list(
        resulted_print = interaction_output
    )
    
    venv_exists = False
    if venv_name in folders:
        venv_exists = True
    
    print('Venv exists: ' + str(venv_exists))
    return venv_exists
# Check imports and confirm function
def setup_venv_create(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    commands: any,
    configs: any
):
    try: 
        from icebreaker.linux.use import linux_open_directory
        from icebreaker.misc.general import fill_list_values
        from functions.interactions.bridge import bridge_ssh_interface
        from icebreaker.lmod.use import lmod_module_command
        from icebreaker.csc.use import csc_create_venv_command
        from icebreaker.python.use import python_venv_activate_command
        from icebreaker.python.utility import python_venv_check_creation
    except ImportError as e:
        raise ImportError("L3_orchestration_dags/actions/setup_actions failed to import", e)

    print('Running venv create')

    venv_modules = configs['venv']['modules']
    venv_path = configs['venv']['path']
    venv_name = configs['venv']['name']

    open_command = linux_open_directory(
        path = venv_path
    )

    module_command = lmod_module_command(
        modules = venv_modules
    )

    create_command = csc_create_venv_command(
        name = venv_name
    )

    activation_command = python_venv_activate_command(
        path = '',
        name = venv_name
    )

    creation_command = fill_list_values(
        target = commands['venv-create'],
        values = [
            open_command,
            module_command,
            create_command,
            activation_command
        ]
    )
    
    interaction_output = bridge_ssh_interface(
        storage_parameters = storage_parameters,
        lock_location = lock_location,
        interaction_parameters = {
            'platform': target_platform,
            'interface': 'ssh',
            'command': creation_command
        }
    )
    #print(interaction_output)
    venv_exists = python_venv_check_creation(
        resulted_print = interaction_output
    )
    print('Venv created: ' + str(venv_exists))
    return venv_exists
# Check imports and confirm function
def setup_venv_packages(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    commands: any,
    configs: any
):
    try: 
        from icebreaker.misc.general import fill_list_values
        from functions.interactions.bridge import bridge_ssh_interface
        from icebreaker.lmod.use import lmod_module_command
        from icebreaker.python.use import python_venv_activate_command
        from icebreaker.python.utility import python_venv_format_packages, python_venv_check_packages
    except ImportError as e:
        raise ImportError("L3_orchestration_dags/actions/setup_actions failed to import", e)

    print('Running venv packages')

    venv_modules = configs['venv']['modules']
    venv_name = configs['venv']['name']
    venv_path = configs['venv']['path']
    venv_packages = configs['venv']['packages']
    
    module_command = lmod_module_command(
        modules = venv_modules
    )

    path_activation_command = python_venv_activate_command(
        path = venv_path,
        name = venv_name
    )

    packages_venv_command = fill_list_values(
        target = commands['venv-packages'],
        values = [
            module_command,
            path_activation_command
        ]
    )
    
    interaction_output = bridge_ssh_interface(
        storage_parameters = storage_parameters,
        lock_location = lock_location,
        interaction_parameters = {
            'platform': target_platform,
            'interface': 'ssh',
            'command': packages_venv_command
        }
    )
    
    package_list = python_venv_format_packages(
        resulted_print = interaction_output
    )
    
    missing_packages = python_venv_check_packages(
        installed_packages = package_list,
        wanted_packages = venv_packages
    )
    print('Found missing packages:', missing_packages)
    return missing_packages
# Check imports and confirm function
def setup_venv_install(
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    commands: any,
    configs: any
):
    try: 
        from icebreaker.misc.general import fill_list_values
        from icebreaker.lmod.use import lmod_module_command
        from functions.interactions.bridge import bridge_ssh_interface
        from icebreaker.python.use import python_venv_activate_command, python_venv_install_command
        from icebreaker.python.utility import python_venv_check_installation
    except ImportError as e:
        raise ImportError("L3_orchestration_dags/actions/setup_actions failed to import", e)

    print('Running venv install')

    venv_modules = configs['venv']['modules']
    venv_packages = configs['venv']['packages']
    venv_name = configs['venv']['name']
    venv_path = configs['venv']['path']

    module_command = lmod_module_command(
        modules = venv_modules
    )

    path_activation_command = python_venv_activate_command(
        path = venv_path,
        name = venv_name
    )
    
    package_command = python_venv_install_command(
        wanted_packages = venv_packages
    )

    install_command = fill_list_values(
        target = commands['venv-install'],
        values = [
            module_command, 
            path_activation_command, 
            package_command
        ]
    )

    interaction_output = bridge_ssh_interface(
        storage_parameters = storage_parameters,
        lock_location = lock_location,
        interaction_parameters = {
            'platform': target_platform,
            'interface': 'ssh',
            'command': install_command
        }
    )
    
    venv_installed = python_venv_check_installation(
        resulted_print = interaction_output
    )
    print('Packages installed: ' + str(venv_installed))
    return venv_installed
# Check imports and confirm function
def setup_send_file(
    swift_client: any,
    bucket_parameters: any,
    storage_parameters: any,
    lock_location: str,
    target_platform: str,
    transfer_source: any,
    transfer_target: any
) -> any:
    try: 
        from icebreaker.storage.management import object_storage_interaction
        from functions.utility.file import file_write_data, file_chmod_command
        from functions.utility.sftp import stfp_store_file
        from functions.interactions.bridge import bridge_ssh_interface
        from functions.actions.sftp import sftp_get_directory_list
    except ImportError as e:
        raise ImportError("L3_orchestration_dags/actions/setup_actions failed to import", e)

    print('Run send file')

    source_place_split = transfer_source['place'].split('/')
    send_result = False
    local_file_path = None
    if source_place_split[0] == 'storage':
        if source_place_split[1] == 'allas':
            source_path_split = transfer_source['path'].split('/')[1:]
            
            bucket_source = source_place_split[-1]
            file_object = object_storage_interaction(
                storage_client = swift_client,
                lock_parameters = storage_parameters['lock'],
                lock_location = lock_location,
                parameters = {
                    'mode': 'get',
                    'bucket-target': bucket_source,
                    'bucket-prefix': bucket_parameters['prefix'],
                    'bucket-user': bucket_parameters['user'],
                    'object-name': source_path_split[0],
                    'path-replacers': {
                        'name': source_path_split[1]
                    },
                    'path-names': source_path_split[2:],
                    'overwrite': True
                },
                object_data = None,
                object_metadata = None
            )
            file_data = file_object[0]
            
            local_file_path = file_write_data(
                name = source_path_split[-1],
                data = file_data
            )

    if source_place_split[0] == 'local':
        source_path_split = transfer_source['path'].split('/')[1:]
        if source_path_split[0] == 'run':
            local_file_path = transfer_source['path']
    
    if not local_file_path is None:
        remote_file_path = transfer_target['path']
        
        store_command = stfp_store_file(
            local_file_path = local_file_path,
            remote_file_path = remote_file_path
        )
        
        send_result = bridge_ssh_interface(
            storage_parameters = storage_parameters,
            lock_location = lock_location,
            interaction_parameters = {
                'platform': target_platform,
                'interface': 'sftp',
                'command': store_command
            }
        )

        remote_file_path_split = remote_file_path.split('/')
        remote_directory = '/'.join(remote_file_path_split[:-1])

        file_list = sftp_get_directory_list(
            storage_parameters = storage_parameters,
            lock_location = lock_location,
            target_platform = target_platform,
            target_path = remote_directory
        )

        remote_file_name = remote_file_path_split[-1]
        if remote_file_name in file_list:
            send_result = True
            if '.pem' in remote_file_name:
                chmod_command = file_chmod_command(
                    file_path = remote_file_path
                )
                # Could be worthwhile to check if a file has permissions
                chmod_result = bridge_ssh_interface(
                    storage_parameters = storage_parameters,
                    lock_location = lock_location,
                    interaction_parameters = {
                        'platform': target_platform,
                        'interface': 'ssh',
                        'command': chmod_command
                    }
                )
    print('Send result: ' + str(send_result))
    return send_result