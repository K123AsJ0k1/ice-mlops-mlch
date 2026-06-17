def swift_client_check(
    storage_client: any
) -> bool:
    try:
        import swiftclient as sc
    except ImportError as e:
        raise ImportError("swift/setup failed to import", e)

    return isinstance(storage_client, sc.Connection)

def swift_get_parameters(
    secret_parameters: any
) -> dict:
    try:
        import time
        from keystoneauth1 import loading, session
        from keystoneauth1.identity import v3
    except ImportError as e:
        raise ImportError("swift/setup failed to import", e)

    swift_auth_url = secret_parameters['swift-auth-url']
    swift_application_credential_id = secret_parameters['swift-application-credential-id']
    swift_application_credential_secret = secret_parameters['swift-application-credential-secret']
    swift_auth_version = secret_parameters['swift-auth-version']
    swift_project_name = secret_parameters['swift-project-name']
    swift_user_domain_name = secret_parameters['swift-domain-name']
    swift_project_domain_name = secret_parameters['swift-domain-name']
    swift_pre_auth_url = secret_parameters['swift-pre-auth-url']

    auth_plugin = None
    if 0 < len(swift_application_credential_id) and 0 < len(swift_application_credential_secret):
        auth_plugin = v3.ApplicationCredential(
            auth_url = swift_auth_url,
            application_credential_id = swift_application_credential_id,
            application_credential_secret = swift_application_credential_secret
        )
    else:
        swift_user = secret_parameters['swift-user']
        swift_key = secret_parameters['swift-key']
        loader = loading.get_plugin_loader('password')
        auth_plugin = loader.load_from_options(
            auth_url = swift_auth_url,
            username = swift_user,
            password = swift_key,
            project_name = swift_project_name,
            user_domain_name = swift_user_domain_name,
            project_domain_name = swift_project_domain_name
        )

    keystone_session = session.Session(
        auth = auth_plugin
    )
    last_auth_time = time.time()
    swift_token = keystone_session.get_token()
    
    swift_parameters = {
        'last-auth-time': last_auth_time,
        'credential-id': str(swift_application_credential_id),
        'credential-secret': str(swift_application_credential_secret),
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

def swift_renew_client(
    secret_parameters: any,
    swift_client: any
) -> any:
    try:
        import time
    except ImportError as e:
        raise ImportError("swift/setup failed to import", e)
    # Tokens expire in 8 hours
    client_refresh_interval = 4 * 60 * 60 
    last_auth_time = secret_parameters['last-auth-time']
    elapsed_time = time.time() - last_auth_time
    new_swift_client = swift_client
    if client_refresh_interval <= elapsed_time:
        new_swift_parameters = swift_get_parameters(
            secret_parameters = secret_parameters
        )

        new_swift_client = swift_setup_client(
            swift_parameters = new_swift_parameters
        )
    return new_swift_client
