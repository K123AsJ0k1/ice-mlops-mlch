def swift_create_or_update_object( 
    swift_client: any,
    bucket_name: str, 
    object_path: str, 
    object_data: any,
    object_metadata: any
) -> any:
    try:
        from .utility import swift_set_encoded_metadata
    except ImportError as e:
        raise ImportError("swift/use failed to import", e)

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
    try:
        from .utility import swift_get_general_metadata, swift_get_decoded_metadata
    except ImportError as e:
        raise ImportError("swift/use failed to import", e)

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
        from .utility import swift_get_general_metadata, swift_get_decoded_metadata
    except ImportError as e:
        raise ImportError("swift/use failed to import", e)

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
        from .utility import swift_get_bucket_metadata, swift_format_bucket_objects
    except ImportError as e:
        raise ImportError("swift/use failed to import", e)

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

def swift_define_object(
    local_path: str,
    object_path: str
) -> any:
    try:
        from swiftclient.service import SwiftUploadObject
    except ImportError as e:
        raise ImportError("swift/use failed to import", e)

    try:
        upload_object = SwiftUploadObject(
            source = local_path,
            object_name = object_path
        )
        return upload_object
    except Exception as e:
        return None
    
def swift_upload_objects(
    swift_options: dict,
    bucket_name: str,
    object_list: list
) -> bool:
    try:
        from swiftclient.service import SwiftService, SwiftError, SwiftUploadObject
    except ImportError as e:
        raise ImportError("swift/use failed to import", e)

    try:
        with SwiftService(options = swift_options) as swift:
            try:
                for r in swift.upload(container = bucket_name, objects = object_list, options = {'segment_size': 5000000000}):
                    if r['success']:
                        if 'object' in r:
                            print(r['object'])
                        elif 'for_object' in r:
                            print(r['for_object'],r['segment_index'])
                    else:
                        error = r['error']
                        if r['action'] == "create_container":
                            print('Create container error', error)
                        elif r['action'] == "upload_object":
                            print('Upload object error', error)
                        else:
                            print('General error', error)
            except SwiftError as e:
                print('SwiftService error', e)
        return True
    except Exception as e:
        print('Swift upload object', e)
        return False
    
# Create download for large objects at some point