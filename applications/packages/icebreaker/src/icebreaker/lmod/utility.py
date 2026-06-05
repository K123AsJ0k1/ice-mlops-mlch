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