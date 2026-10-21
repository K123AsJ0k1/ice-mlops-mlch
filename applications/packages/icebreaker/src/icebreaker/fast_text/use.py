
def fasttext_chinese_check(
    text: str
) -> bool:
    try:
        import re
    except ImportError as e:
        raise ImportError("fast_text/utility failed to import", e)

    pattern = r'[\u4e00-\u9fff]'
    return bool(re.search(pattern, text))

def fasttext_get_languages(
    model: any,
    texts: list,
    default_label: str,
    confidence_threshold: float,
    label_replacer: any 
): 
    results = {
        'predictions': [],
        'default-amount': 0
    }
    
    for content in texts:
        chinese_check = fasttext_chinese_check(
            text = content
        )

        if not chinese_check:
            cleaned_text = content.replace('\n', ' ')
            
            labels, confidences = model.predict(cleaned_text, k=1)  
            language_label = labels[0].replace('__label__', '')
            label_confidence = float(confidences[0])

            if 0 < len(label_replacer):
                if language_label in label_replacer:
                    language_label = label_replacer[language_label]

            if not language_label == default_label:
                if label_confidence < confidence_threshold:
                    language_label = default_label
                    label_confidence = 0.0
                    results['default-amount'] += 1
        else:
            language_label = 'zh'
            label_confidence = 1.0
        
        results['predictions'].append((language_label, label_confidence))
    
    return results

def fasttext_get_data(
    model: any,
    texts: list,
    default_label: str,
    confidence_threshold: float,
    label_replacer: any,
    stat_mode: bool
):  
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("fast_text/utility failed to import", e)

    results = fasttext_get_languages(
        model = model,
        texts = texts,
        default_label = default_label,
        confidence_threshold = confidence_threshold,
        label_replacer = label_replacer
    ) 

    used_columns = [
        'language',
        'language-confidence'
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