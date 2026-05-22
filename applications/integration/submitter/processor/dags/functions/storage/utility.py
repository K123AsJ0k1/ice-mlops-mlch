def create_object_index(
    object_path: str,
    bucket_objects: any
) -> str:
    largest_key = 0
    for name in bucket_objects.keys():
        target_path_split = object_path.split('/')
        path = name.split('.')[0]
        comparison_path_split = path.split('/')
        if len(target_path_split) == len(comparison_path_split):
            found = True
            for i in range(0, len(target_path_split)-1):
                if not target_path_split[i] == comparison_path_split[i]:
                    found = False     
            if found:
                used_key = comparison_path_split[-1]
                if used_key.isnumeric():
                    used_key = int(used_key)
                    if largest_key < used_key:
                        largest_key = used_key
    new_key = largest_key + 1
    new_key = str(new_key)
    return new_key

