def linux_format_pwd(
    given_print: str
) -> str:
    formatted = given_print.split('\n')[0]
    directory = None
    if '/' in formatted:
        directory = formatted
    return directory

def linux_format_list(
    resulted_print: str
) -> str:
    formatted_names = resulted_print.split('\n')[:-1]
    folders = []
    files = []
    for name in formatted_names:
        if '.' in name:
            files.append(name)
        else:
            folders.append(name)
    return folders, files