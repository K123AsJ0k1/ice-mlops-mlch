import re

def lmod_parse_list(
    given_print: str
) -> any:
    pattern = r'(\d+\)\s*) ([a-z-/0-9.A-Z_]*)'
    module_list = re.findall(pattern, given_print)
    ordered_modules = [None] * len(module_list)
    for number, module in module_list:
        list_index = int(number[:-1])-1
        ordered_modules[list_index] = module
    return ordered_modules

def lmod_module_command(
    modules: any
) -> str:
    string_command = ''
    template_prefix = 'module '
    for module in modules:
        if 'use' in module or 'load' in module:
            if len(string_command) == 0:
                string_command = template_prefix + module
                continue
            string_command += ' && ' + template_prefix + module 
    return string_command

def lmod_list_command() -> str:
    return 'module list 2>&1'