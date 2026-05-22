def python_parse_version(
    given_print: str
) -> any:
    formatted_version = given_print.split('\n')[0]
    version = None
    if 'Python' in formatted_version:
        version = formatted_version.split(' ')[1]
    return version

def python_version_command() -> str:
    return 'python3 -V'