def swift_client_check(
    storage_client: any
) -> any:
    try:
        import swiftclient as sc
    except ImportError as e:
        raise ImportError("swift/setup failed to import", e)

    return isinstance(storage_client, sc.Connection)

def swift_get_parameters(
    secret_parameters: any
):
    try:
        from keystoneauth1 import loading, session
    except ImportError as e:
        raise ImportError("swift/setup failed to import", e)

    swift_auth_url = secret_parameters['swift-auth-url']
    swift_auth_version = secret_parameters['swift-auth-version']
    swift_user = secret_parameters['swift-user']
    swift_key = secret_parameters['swift-key']
    swift_project_name = secret_parameters['swift-project-name']
    swift_user_domain_name = secret_parameters['swift-domain-name']
    swift_project_domain_name = secret_parameters['swift-domain-name']
    swift_pre_auth_url = secret_parameters['swift-pre-auth-url']

    loader = loading.get_plugin_loader('password')
    auth = loader.load_from_options(
        auth_url = swift_auth_url,
        username = swift_user,
        password = swift_key,
        project_name = swift_project_name,
        user_domain_name = swift_user_domain_name,
        project_domain_name = swift_project_domain_name
    )

    keystone_session = session.Session(
        auth = auth
    )
    swift_token = keystone_session.get_token()
    
    swift_parameters = {
        'pre-auth-token': str(swift_token),
        'pre-auth-url': str(swift_pre_auth_url),
        'auth-version': str(swift_auth_version),
        'project-name': str(swift_project_name),
        'user-domain-name': str(swift_user_domain_name),
        'project-domain-name': str(swift_project_domain_name)
    }

    return swift_parameters

def swift_setup_client(
    swift_parameters: any
) -> any:
    try:
        import swiftclient as sc
    except ImportError as e:
        raise ImportError("swift/setup failed to import", e)
        
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

