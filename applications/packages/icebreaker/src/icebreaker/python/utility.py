def python_parse_version(
    given_print: str
) -> any:
    formatted_version = given_print.split('\n')[0]
    version = None
    if 'Python' in formatted_version:
        version = formatted_version.split(' ')[1]
    return version

def python_venv_format_packages(
    resulted_print: str
) -> any:
    try:
        import re
    except ImportError as e:
        raise ImportError("python/utility failed to import", e)

    pattern = re.compile(r"^(\S+)\s+(\S+)$", re.MULTILINE)
    matches = pattern.finditer(resulted_print)
    venv_packages = {}
    filtered_names = [
        'Package',
        '----------------------------------------',
        'Documentation:',
        'Support:'
    ]
    for match in matches:
        package = match.group(1)
        version = match.group(2)
        if package not in filtered_names:
            venv_packages[package] = version
    return venv_packages

def python_venv_check_packages(
    installed_packages: any,
    wanted_packages: any
) -> any:
    try:
        import re
    except ImportError as e:
        raise ImportError("python/utility failed to import", e)

    missing_packages = []
    for package_info in wanted_packages:
        used_package_info = package_info
        if '-f' in used_package_info:
            used_package_info = used_package_info.replace(' ', '')
            used_package_info = used_package_info.split('-f')[0]
        if '"' in used_package_info:
            used_package_info = used_package_info.replace('"','')
        if '[' in package_info:    
            used_package_info = re.sub(r'\[.*\]', '', used_package_info)
        if '==' in used_package_info:
            info_split = used_package_info.split('==')
            formatted_name = info_split[0]
            formatted_version = info_split[1]
        else:
            formatted_name = used_package_info
            formatted_version = None
        
        if not formatted_name in installed_packages:
            missing_packages.append(package_info)
        else:
            if not formatted_version is None:
                if not installed_packages[formatted_name] == formatted_version:
                    missing_packages.append(package_info)
    return missing_packages

def python_venv_error_check(
    resulted_print: str
) -> bool:
    try:
        import re
    except ImportError as e:
        raise ImportError("python/utility failed to import", e)

    error_patterns = {
        "conflict": r"ERROR: Cannot install .*? (?=ERROR:|\Z)",
        "no_match": r"ERROR: No matching distribution found for .*? (?=ERROR:|\Z)",
        "network": r"Could not fetch URL .*? (?=ERROR:|\Z)",
        "permission": r"Permission denied",
    }
    
    found_errors = []
    for category, pattern in error_patterns.items():
        match = re.search(pattern, resulted_print, re.DOTALL | re.IGNORECASE)
        if match:
            found_errors.append(f"{category.upper()}: {match.group(0).strip()}")
    return found_errors

def python_venv_check_creation(
    resulted_print: str
) -> bool:
    try:
        import re
    except ImportError as e:
        raise ImportError("python/utility failed to import", e)

    errors = python_venv_error_check(
        resulted_print = resulted_print
    )
    
    success = False
    if len(errors) == 0:
        pip_update_check = re.search(r'Successfully installed pip-\d+', resulted_print)
        pip_requirement_check = re.search(r'Requirement already satisfied: pip', resulted_print)
        
        if pip_update_check or pip_requirement_check:
            success = True
    return success

def python_venv_check_installation(
    resulted_print: str
) -> bool:
    try:
        import re
    except ImportError as e:
        raise ImportError("python/utility failed to import", e)

    errors = python_venv_error_check(
        resulted_print = resulted_print
    )

    success = False
    if len(errors) == 0:
        pip_install_check = re.search(r'Successfully installed .*', resulted_print)
        if pip_install_check:
            success = True
    return success