---
technologies: "SWIFT"
category: "Choice and use of technology"
difficulty: "Intermediate"
---

# SWIFT

## Used material

1. <span id="used-material-1"></span> [Accessing Allas](https://docs.csc.fi/data/Allas/accessing_allas/)

2. <span id="used-material-2"></span> [Using Allas with Python and SWIFT protocol](https://docs.csc.fi/data/Allas/using_allas/python_swift/)

3. <span id="used-material-3"></span> [Application credentials](https://docs.csc.fi/cloud/pouta/application-credentials/)

4. <span id="used-material-4"></span> [python-decouple pip package](https://pypi.org/project/python-decouple/)

5. <span id="used-material-5"></span> [keystoneauth1 pip package](https://pypi.org/project/keystoneauth1/)

6. <span id="used-material-6"></span> [python-keystoneclient pip package](https://pypi.org/project/python-keystoneclient/)

7. <span id="used-material-7"></span> [python-swiftclient pip package](https://pypi.org/project/python-swiftclient/)

## Why use SWIFT? 

The OpenStack Python SWIFT client is the most capable library for accessing the Allas object storage provided by the Center of Scientific Computing (CSC). The SWIFT client is widely used for the following reasons:

- Provides an official implementation for OpenStack object storage interactions, has been widely tested by the OpenStack community, and enables integration with OpenStack identity services (mature)

- Enables CLI and client tools, automatic large object handling, and a high-level service API (abstracted)

- Supports various OpenStack identity configurations, passing session authentication between clients and cross-language utilization with standard dictionaries (interoperable)  

These features make SWIFT the default object storage library for storing and fetching various objects, simplifying Allas utilization across different hardware and infrastructures.

## How to use SWIFT?

Assuming you have Allas access mentioned in the [Allas chapter](./01_allas.md), we can start using SWIFT client |[(1)](#used-material-1), [(2)](#used-material-2)| by creating application credentials by following [(3)](#used-material-3). When credential with object_storage_role has been created, use the given ID and secret to create a file with the path /home/$USER/.ssh/.env in the following way:

1. Open a terminal

2. Run the following commands

```
cd .ssh
nano .env
```

3. Add the following details into the file

```
CSC_PROJECT_1_CRED_ID = "[The ID given during creation]"
CSC_PROJECT_1_CRED_SECRET = "[The secret given during creation]"
CSC_PROJECT_1 = "[project_(MyCSC number)]"
CSC_USER_DOMAIN_NAME = "Default"
```

4. Save the file with

```
CTRL + X 
Y
```

5. Install the following PIP package [(4)](#used-material-4)

```
pip install python-decouple
```

6. Setup the secret values with following code

```
from decouple import Config,RepositoryEnv
env_path = '/home/$USER/.ssh/.env'
env_dict = Config(RepositoryEnv(env_path))
swift_credential_id = env_dict.get('CSC_PROJECT_1_CRED_ID')
swift_credential_secret = env_dict.get('CSC_PROJECT_1_CRED_SECRET')
swift_project_name = env_dict.get('CSC_PROJECT_1')
swift_domain_name = env_dict.get('CSC_USER_DOMAIN_NAME')

secret_parameters = {
    'auth-url': '[cPouta Dashboard API Access Identity Service Endpoint]',
    'credential-id': swift_credential_id,
    'credential-secret': swift_credential_secret,
    'auth-version': '3',
    'project-name': swift_project_name,
    'user-domain-name': swift_domain_name,
    'project-domain-name': swift_domain_name,
    'pre-auth-url': '[cPouta Dashboard API Access Object Store Service Endpoint]'
}
```

7. Install the following packages |[(5)](#used-material-5), [(6)](#used-material-6), [(7)](#used-material-7)|

```
pip install keystoneauth1
pip install python-keystoneclient
pip install python-swiftclient
```

8. Get a sharable SWIFT token and put it into swift parameters

```
from keystoneauth1 import loading, session
from keystoneauth1.identity import v3
auth_plugin = v3.ApplicationCredential(
    auth_url = swift_auth_url,
    application_credential_id = swift_application_credential_id,
    application_credential_secret = swift_application_credential_secret
)

keystone_session = session.Session(
    auth = auth_plugin
)
last_auth_time = time.time()
swift_token = keystone_session.get_token()

swift_parameters = {
    'last-auth-time': last_auth_time,
    'auth-url': str(swift_auth_url),
    'credential-id': str(swift_application_credential_id),
    'credential-secret': str(swift_application_credential_secret),
    'pre-auth-token': str(swift_token),
    'pre-auth-url': str(swift_pre_auth_url),
    'auth-version': str(swift_auth_version),
    'project-name': str(swift_project_name),
    'user-domain-name': str(swift_user_domain_name),
    'project-domain-name': str(swift_project_domain_name)
}
```

9. Create a SWIFT client for interactions

```
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
```

10. Tokens expire in 8 hours, so run steps 8-9 to maintain connection

## SWIFT Abstraction

The Python SWIFT client uses PUT, CREATE, GET, DELETE, and LIST functions to manage bucket and object creation. The number of these commands and their different outputs with metadata formats make direct use of the client's high-level functions more complex and time-consuming in different scenarios, which is why our use case will abstract the functions, interactions and serialization. These form the following function structure:

- Function level 
    - Setup 
        - Client check
        - Swift parameters
        - Swift client
        - Renew client
    - Use 
        - Create and update object
        - Check object metadata
        - Get object content
        - Remove object
        - Get bucket info
        - Get container info
        - Define object
        - Upload objects
    - Utility
        - Set encoded metadata
        - Get general metadata
        - Get decoded metadata 
        - Get bucket metadata
        - Format bucket objects
- Interaction level
    - Management
        - Set bucket name
        - Set object path
        - Object storage interaction
- Serialization level
    - Use
        - Store data
        - Get data
        - Nested update

The function level hides SWIFT client details and provides try-except blocks to prevent runtime errors, which the interaction level uses to simplify use with parameters and provide concurrency locking, while the serialization level simplifies use of different serialization types with parameters. This enables using serialization-level functions when possible, with code needing to use interaction-level functions only when necessary.

---