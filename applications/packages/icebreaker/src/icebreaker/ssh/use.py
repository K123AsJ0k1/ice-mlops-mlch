import re

def ssh_create_command(
    commands: any
) -> str:
    string_command = ''
    if isinstance(commands, list):
        for command in commands:
            if len(string_command) == 0:
                string_command = command
                continue
            string_command += ' && ' + command
    return string_command

def ssh_check_command(
    string_command: str
) -> bool:
    # This is too strict
    # Accepts single or && chained commands
    pattern = r"^[^&|;]+(?:\s+&&\s+[^&|;]+)*$"
    return bool(re.match(pattern, string_command.strip()))
