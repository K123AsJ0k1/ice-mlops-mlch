import swiftclient as sc

def swift_client_check(
    storage_client: any
) -> any:
    return isinstance(storage_client, sc.Connection)

def swift_setup_client(
    swift_parameters: any
) -> any:
    swift_client = sc.Connection(
        preauthurl = swift_parameters['pre-auth-url'],
        preauthtoken = swift_parameters['pre-auth-token'],
        os_options = {
            'user_domain_name': swift_parameters['user-domain-name'],
            'project_domain_name': swift_parameters['project-domain-name'],
            'project_name': swift_parameters['project-name']
        },
        auth_version = swift_parameters['auth-version']
    )
    return swift_client