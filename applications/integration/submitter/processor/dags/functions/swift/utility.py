def swift_set_encoded_metadata(
    metadata: any
) -> any:
    encoded_metadata = {}
    key_initial = 'x-object-meta'
    for key, value in metadata.items():
        encoded_key = key_initial + '-' + key
        if isinstance(value, list):
            encoded_metadata[encoded_key] = 'list=' + ','.join(map(str, value))
            continue
        encoded_metadata[encoded_key] = str(value)
    return encoded_metadata

def swift_get_general_metadata(
    metadata: any
) -> any:
    general_metadata = {}
    key_initial = 'x-object-meta'
    for key, value in metadata.items():
        if not key_initial == key[:len(key_initial)]:
            general_metadata[key] = value
    return general_metadata

def swift_get_decoded_metadata(
    metadata: any
) -> any:
    decoded_metadata = {}
    key_initial = 'x-object-meta'
    for key, value in metadata.items():
        if key_initial == key[:len(key_initial)]:
            decoded_key = key[len(key_initial) + 1:]
            if 'list=' in value:
                string_integers = value.split('=')[1]
                values = string_integers.split(',')
                if len(values) == 1 and values[0] == '':
                    decoded_metadata[decoded_key] = []
                else:
                    try:
                        decoded_metadata[decoded_key] = list(map(int, values))
                    except:
                        decoded_metadata[decoded_key] = list(map(str, values))
                continue
            if value.isnumeric():
                decoded_metadata[decoded_key] = int(value)
                continue
            decoded_metadata[decoded_key] = value
    return decoded_metadata

def swift_get_bucket_metadata(
    metadata: any
):
    relevant_values = {
        'x-container-object-count': 'object-count',
        'x-container-bytes-used-actual': 'used-bytes',
        'last-modified': 'date',
        'content-type': 'type'
    }
    formatted_metadata = {}
    for key,value in metadata.items():
        if key in relevant_values:
            formatted_key = relevant_values[key]
            formatted_metadata[formatted_key] = value
    return formatted_metadata

def swift_format_bucket_objects(
    objects: any
) -> any:
    formatted_objects = {}
    for bucket_object in objects:
        formatted_object_metadata = {
            'hash': 'id',
            'bytes': 'used-bytes',
            'last_modified': 'date'
        }
        object_key = None
        object_metadata = {}
        for key, value in bucket_object.items():
            if key == 'name':
                object_key = value
            if key in formatted_object_metadata:
                formatted_key = formatted_object_metadata[key]
                object_metadata[formatted_key] = value
        formatted_objects[object_key] = object_metadata
    return formatted_objects