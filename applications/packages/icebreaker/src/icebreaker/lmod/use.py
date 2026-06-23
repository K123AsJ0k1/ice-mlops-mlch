
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