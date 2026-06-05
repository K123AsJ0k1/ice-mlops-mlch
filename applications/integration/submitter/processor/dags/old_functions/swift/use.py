from functions.swift.utility import swift_get_decoded_metadata, swift_get_general_metadata, swift_set_encoded_metadata, swift_get_bucket_metadata, swift_format_bucket_objects

def swift_create_or_update_object( 
    swift_client: any,
    bucket_name: str, 
    object_path: str, 
    object_data: any,
    object_metadata: any
) -> any:
    bucket_info = {}
    
    try:
        given_info = swift_client.get_container(
                container = bucket_name
            )
        bucket_info = {
            'metadata': given_info[0],
            'objects': given_info[1]
        }
    except Exception as e:
        pass

    if len(bucket_info) == 0:
        try:
            swift_client.put_container(
                container = bucket_name
            )
        except Exception as e:
            return False
    
    object_info = {}
    try:
        object_info = swift_client.head_object(
            container = bucket_name,
            obj = object_path
        )       
    except Exception as e:
        pass
    
    if not len(object_info) == 0:
        try:
            swift_client.delete_object(
                container = bucket_name, 
                obj = object_path
            )
        except Exception as e:
            return False
        
    formatted_metadata = swift_set_encoded_metadata(
        metadata = object_metadata
    )
    
    try:
        # Add 5GB addition later
        swift_client.put_object(
            container = bucket_name,
            obj = object_path,
            contents = object_data,
            headers = formatted_metadata
        )
        return True
    except Exception as e:
        return False
    
def swift_check_object_metadata(
    swift_client: any,
    bucket_name: str, 
    object_path: str
) -> any:
    all_metadata = {}
    try:
        all_metadata = swift_client.head_object(
            container = bucket_name,
            obj = object_path
        )       
    except Exception as e:
        pass

    object_metadata = {
        'general-meta': {},
        'custom-meta': {}
    }
    if not len(all_metadata) == 0:
        general_metadata = swift_get_general_metadata(
            metadata = all_metadata
        )
        custom_metadata = swift_get_decoded_metadata(
            metadata = all_metadata
        )

        object_metadata['general-meta'] = general_metadata
        object_metadata['custom-meta'] = custom_metadata
    
    return object_metadata

def swift_get_object_content(
    swift_client: any,
    bucket_name: str,
    object_path: str
) -> any:
    try: 
        response = swift_client.get_object(
            container = bucket_name,
            obj = object_path 
        )
        general_meta = swift_get_general_metadata(
            metadata = response[0]
        )
        custom_meta = swift_get_decoded_metadata(
            metadata = response[0]
        )
        object_content = {
            'data': response[1],
            'general-meta': general_meta,
            'custom-meta': custom_meta
        }
        return object_content
    except Exception as e:
        return {}

def swift_remove_object(
    swift_client: any,
    bucket_name: str,
    object_path: str   
) -> bool:
    try:
        swift_client.delete_object(
            container = bucket_name, 
            obj = object_path
        )
        return True
    except Exception as e:
        return False
    
def swift_get_bucket_info(
    swift_client: any,
    bucket_name: str   
) -> any:
    try:
        bucket_info = swift_client.get_container(
            container = bucket_name
        )
        bucket_metadata = swift_get_bucket_metadata(
            metadata = bucket_info[0]
        )
        bucket_objects = swift_format_bucket_objects(
            objects = bucket_info[1]
        )
        return {'metadata': bucket_metadata, 'objects': bucket_objects} 
    except Exception as e:
        return {} 

def swift_get_container_info(
    swift_client: any
) -> any:
    try:
        account_buckets = swift_client.get_account()[1]
        container_info = {}
        for bucket in account_buckets:
            bucket_name = bucket['name']
            bucket_count = bucket['count']
            bucket_size = bucket['bytes']
            container_info[bucket_name] = {
                'amount': bucket_count,
                'size': bucket_size
            }
        return container_info 
    except Exception as e:
        return {}