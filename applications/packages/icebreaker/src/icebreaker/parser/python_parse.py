 
def python_check_main(
    node: any
) -> bool:
    try:
        import ast
    except ImportError as e:
        raise ImportError("parser/python_parse failed to import", e)

    if not isinstance(node, ast.If):
        return False
    
    test = node.test
    if isinstance(test, ast.Compare):
        if isinstance(test.left, ast.Name) and test.left.id == "__name__":
            if isinstance(test.ops[0], ast.Eq):
                comparators = test.comparators[0]
                if isinstance(comparators, ast.Constant) and comparators.value == "__main__":
                    return True
    return False

def python_relevant_imports(
    node: any, 
    imports: any
):
    try:
        import ast
    except ImportError as e:
        raise ImportError("parser/python_parse failed to import", e)

    used_names = set()
    for walk_node in ast.walk(node):
        if isinstance(walk_node, ast.Name):
            used_names.add(walk_node.id)
        elif isinstance(walk_node, ast.Attribute):
            if isinstance(walk_node.value, ast.Name):
                used_names.add(walk_node.value.id)

    relevant_import_strings = []
    
    for imp in imports:
        if isinstance(imp, ast.Import):
            for alias in imp.names:
                name_to_check = alias.asname if alias.asname else alias.name
                if name_to_check in used_names:
                    relevant_import_strings.append(ast.unparse(imp))
                    break 
        elif isinstance(imp, ast.ImportFrom):
            for alias in imp.names:
                name_to_check = alias.asname if alias.asname else alias.name
                if name_to_check in used_names:
                    relevant_import_strings.append(ast.unparse(imp))
                    break
                    
    return relevant_import_strings

def python_get_router(
    tree: any
) -> any:
    try:
        import ast
    except ImportError as e:
        raise ImportError("parser/python_parse failed to import", e)

    router_line = ''
    for node in tree.body:
        if isinstance(node, ast.Assign):
            node_code = ast.unparse(node)
            if "APIRouter(" in node_code:
                router_line = node_code
    return router_line

def python_get_celery(
    tree: any
) -> any:
    try:
        import ast
    except ImportError as e:
        raise ImportError("parser/python_parse failed to import", e)

    celery_line = ''
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Call):
                node_code = ast.unparse(node)
                if "celery_setup_instance(" in node_code:
                    celery_line = node_code
    return celery_line

def python_parse_file(
    file_path: str,
    absolute_path: str
):
    try:
        import ast
    except ImportError as e:
        raise ImportError("parser/python_parse failed to import", e)

    content = None
    with open(file_path, 'r') as f:
        content = f.read()

    tree = ast.parse(content)
    imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    
    file_path_split = absolute_path.split('/')
    used_directory = file_path_split[-2]
    used_file = file_path_split[-1].split('.')[0]
    parsed_material = []
    for node in tree.body:
        is_main = python_check_main(
            node = node
        )
        # This should only handle classes and functions
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) or is_main:
            fastapi_case = False
            header = f'Python {used_directory} {used_file} '
            if isinstance(node, (ast.FunctionDef)):
                name = node.name
                header += f'function {name}'
            if isinstance(node, (ast.ClassDef)):
                name = node.name
                header += f'class {name}'
            if isinstance(node, (ast.AsyncFunctionDef)):
                name = node.name
                header += f'FastAPI route {name}'
                fastapi_case = True
            
            if is_main:
                header += f'main'
            
            relevant_imports = python_relevant_imports(
                node = node, 
                imports = imports
            )

            node_code = ast.unparse(node)

            formatted_content = f'## {header}\n\n'
            formatted_content += f'This is from:{absolute_path}\n'
            formatted_content += f'```python\n'
            if 0 < len(relevant_imports):
                import_block = "\n".join(relevant_imports)
                formatted_content += f'{import_block}\n\n'
            if fastapi_case:
                router_line = python_get_router(
                    tree = tree
                )
                formatted_content += f'{router_line}\n\n'
            if '_celery.task' in node_code:
                celery_line = python_get_celery(
                    tree = tree
                )
                
                formatted_content += f'{celery_line}\n\n'
            
            formatted_content += f'{node_code}\n```'
            
            parsed_material.append({
                'metadata': {}, 
                'topic': header,
                'material': {},
                'content': formatted_content,
                'paths': {}
            })
    return parsed_material