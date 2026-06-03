
import os
import yaml
import pickle
import time
from decouple import Config,RepositoryEnv
from icebreaker.swift.setup import swift_get_parameters, swift_setup_client 
from icebreaker.swift.use import swift_get_object_content
from icebreaker.misc.dict import check_dict_path, get_dict_value
from icebreaker.docker.use import docker_manage_compose
from icebreaker.logger.setup import logger_setup_configuration

def setup_controller(
    input_path: str
):
    logger = logger_setup_configuration(
        logger_name = 'controller'
    )
    
    logger.info("Starting Ray-Chisel micro-controller")

    logger.info('Getting input file')
    if not os.path.exists(input_path):
        logger.info(f"Error: File not found at {input_path}")
        return False

    yaml_dict = {}
    with open(input_path, 'r') as f:
        yaml_dict = yaml.safe_load(f)

    env_path = yaml_dict['env_path']
    logger.info('Getting env file')
    if not os.path.exists(env_path):
        logger.info(f"Error: File not found at {env_path}")
        return False
    
    env_dict = Config(RepositoryEnv(env_path))
    
    swift_user = env_dict.get('CSC_USERNAME')
    swift_password = env_dict.get('CSC_PASSWORD')
    swift_project_name = env_dict.get('CSC_PROJECT_1')
    swift_domain_name = env_dict.get('CSC_USER_DOMAIN_NAME')
    
    swift_token = env_dict.get('SWIFT_TOKEN')
    swift_auth_url = env_dict.get('SWIFT_AUTH_URL')
    swift_auth_version = env_dict.get('SWIFT_AUTH_VERSION')
    swift_pre_auth_url = env_dict.get('SWIFT_PRE_AUTH_URL')
    
    logger.info('Creating swift parameters')
    setup_swift_parameters = {}
    if 0 < len(swift_user) and 0 < len(swift_password):
        logger.info('Username and password exist')
        setup_swift_parameters = swift_get_parameters(
            secret_parameters = {
                'swift-auth-url': swift_auth_url,
                'swift-auth-version': swift_auth_version,
                'swift-user': swift_user,
                'swift-key': swift_password,
                'swift-project-name': swift_project_name,
                'swift-domain-name': swift_domain_name,
                'swift-pre-auth-url': swift_pre_auth_url
            }
        )
    if 0 < len(swift_token):
        logger.info('Token exists')
        setup_swift_parameters = {
            'pre-auth-token': swift_token,
            'pre-auth-url': swift_pre_auth_url,
            'auth-version': swift_auth_version,
            'project-name': swift_project_name,
            'user-domain-name': swift_domain_name,
            'project-domain-name': swift_domain_name,
        }
    
    logger.info('Setting up swift client')
    swift_client = swift_setup_client(
        swift_parameters = setup_swift_parameters
    )

    object_bucket = yaml_dict['object_bucket']
    object_path = yaml_dict['object_path']
    
    controlled_dimension = yaml_dict['controlled_dimension']
    controlled_cluster = yaml_dict['controlled_cluster']
    controlled_path = controlled_dimension + '-clusters-' + controlled_cluster 
    compose_file_path = yaml_dict['compose_path']
    check_interval = yaml_dict['check_interval']
    current_state = "UNKNOWN"
    while True:
        logger.info('Getting cluster')
        object_content = swift_get_object_content(
            swift_client = swift_client,
            bucket_name = object_bucket,
            object_path = object_path
        )
        cluster_yamls = pickle.loads(object_content['data'])

        logger.info(f"Checking dict path: {controlled_path}")
        path_exists = check_dict_path(
            target_dict = cluster_yamls,
            key_path = controlled_path,
            separator = '-'
        )

        if not path_exists:
            break

        cluster_dict = get_dict_value(
            target_dict = cluster_yamls,
            key_path = controlled_path,
            separator = '-'
        )

        current_state = docker_manage_compose(
            file_path = compose_file_path,
            current_state = current_state,
            wanted_state = cluster_dict['activate'],
            print_function = logger.info
        )

        time.sleep(check_interval)