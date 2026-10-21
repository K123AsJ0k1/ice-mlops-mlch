
def magika_block_format(  
    text: str
) -> str:
    try:
        import re
        from collections import Counter
    except ImportError as e:
        raise ImportError("mgka/use failed to import", e)

    pattern = r'```([a-zA-Z0-9_-]+)'
    matches = re.findall(pattern, text, re.MULTILINE)

    if not matches:
        return ('null', {})

    normalized_tags = [tag.lower() for tag in matches]

    counts = Counter(normalized_tags)
    dominant_lang, frequency = counts.most_common(1)[0]
    return dominant_lang, dict(counts)

def magika_get_formats(
    model: any,
    texts: any,
    default_label: str,
    confidence_threshold: float,
    label_replacer: any
):  
    results = {
        'predictions': [],
        'default-amount': 0
    }
    
    for content in texts:
        format_label, counts = magika_block_format(
            text = content
        )
        label_confidence = 1.0

        if format_label == 'null':
            formatted_text = content.encode('utf-8')

            prediction = model.identify_bytes(formatted_text)
            format_label = prediction.output.label
            label_confidence = prediction.score

            if 0 < len(label_replacer):
                if format_label in label_replacer:
                    format_label = label_replacer[format_label]
            
            if not format_label == default_label:
                if label_confidence < confidence_threshold:
                    format_label = default_label
                    label_confidence = 0.0
                    results['default-amount'] += 1
        
        results['predictions'].append((format_label, label_confidence, counts))
    
    return results

def magika_get_data(
    model: any,
    texts: any,
    default_label: str,
    confidence_threshold: float,
    label_replacer: any,
    stat_mode: bool
): 
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("mgka/use failed to import", e)

    results = magika_get_formats(
        model = model,
        texts = texts,
        default_label = default_label,
        confidence_threshold = confidence_threshold,
        label_replacer = label_replacer
    )

    used_columns = [
        'format',
        'format-confidence',
        'format-counts'
    ]

    prediction_df = pd.DataFrame(
        results['predictions'],
        columns = used_columns
    )

    if not stat_mode:
        return {
            'table': prediction_df
        }

    formatted_metrics = {}
    wanted_stats = [
        'size',
        'mean', 
        'std', 
        'median', 
        'min', 
        'max'
    ]

    stats_df = prediction_df.groupby(used_columns[0])[used_columns[1]].agg(wanted_stats).to_dict()
    for name, values in stats_df.items():
        for key, value in values.items():
            flattened_key = f'language-{key}-{name}'
            formatted_metrics[flattened_key] = value
    
    formatted_metrics['language-default-size'] = results['default-amount']

    return {
        'metrics': formatted_metrics,
        'table': prediction_df
    }