
def utility_header_name(
    absolute_path: str,
    start_prefix: str
) -> str:
    file_path_split = absolute_path.split('/')
    header_name = ''
    start_found = False
    for substring in file_path_split:
        if start_prefix in substring and not start_found:
            start_found = True
            header_name += f'{substring}'
            continue
        if start_found:
            header_name += f'/{substring}'
    return header_name

