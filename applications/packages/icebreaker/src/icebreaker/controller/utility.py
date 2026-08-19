def controller_extract_output(
    output: str
):
    try:
        import re
        import json
    except ImportError as e:
        raise ImportError("controller/utility failed to import", e)
    
    json_match = re.search(r"\{.*\}", output, re.DOTALL)
    if not json_match:
        return {
            'reasoning': 'Failed to extract JSON from guardrail output', 
            'secret-leak': 0, 
            'off-topic': 0,
            'irrelevant': 0,
            'verbose': 0,
            'out-of-scope': 0
        }

    json_str = json_match.group(0)

    try:
        data = json.loads(json_str)
        return data
    except Exception as e:
        return {
            'reasoning': 'Malformed JSON returned by guardrail', 
            'secret-leak': 0, 
            'off-topic': 0,
            'irrelevant': 0,
            'verbose': 0,
            'out-of-scope': 0
        }