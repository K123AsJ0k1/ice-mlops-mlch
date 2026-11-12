def controller_extract_output(
    output: str,
    error_default: dict
):
    try:
        import re
        import json
    except ImportError as e:
        raise ImportError("controller/utility failed to import", e)
    
    json_match = re.search(r"\{.*\}", output, re.DOTALL)
    if not json_match:
        return error_default

    json_str = json_match.group(0)

    try:
        data = json.loads(json_str)
        return data
    except Exception as e:
        return error_default