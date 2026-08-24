def judge_extract_output(
    output: str
):
    try:
        import re
        import json
    except ImportError as e:
        raise ImportError("judge/utility failed to import", e)
    
    json_match = re.search(r"\{.*\}", output, re.DOTALL)
    if not json_match:
        return {
            'reasoning': 'Failed to extract JSON from guardrail output', 
            'correctness': 0,
            'faithfulness': 0,
            'relevance': 0,
        }

    json_str = json_match.group(0)

    try:
        data = json.loads(json_str)
        return data
    except Exception as e:
        return {
            'reasoning': 'Malformed JSON returned by guardrail', 
            'correctness': 0,
            'faithfulness': 0,
            'relevance': 0,
        }