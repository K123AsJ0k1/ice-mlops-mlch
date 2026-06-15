
def fasttext_get_stats(
    model: any,
    texts: list,
    default_value: str,
    default_threshold: str,
    label_replacer: any,
    batch_mode: bool
):  
    try:
        import statistics
    except ImportError as e:
        raise ImportError("Failed to import", e)

    collected_statistics = {}
    language_amounts = {}
    language_default_amount = 0
    for content in texts:
        cleaned_text = content.replace('\n', ' ')
        
        labels, confidences = model.predict(cleaned_text, k=1)  
        language_label = labels[0].replace('__label__', '')
        label_confidence = float(confidences[0])

        if 0 < len(label_replacer):
            if language_label in label_replacer:
                language_label = label_replacer[language_label]

        if not language_label == default_value:
            if label_confidence < default_threshold:
                language_label = default_value
                label_confidence = 0.0
                language_default_amount += 1
            
        if not language_label in language_amounts:
            confidence_starting_value = []
            if not label_confidence == 0.0:
                confidence_starting_value.append(label_confidence)
            language_amounts[language_label] = {
                'amount': 1,
                'confidence': confidence_starting_value 
            }
        else:
            language_amounts[language_label]['amount'] += 1
            if not label_confidence == 0.0:
                language_amounts[language_label]['confidence'].append(label_confidence)

    collected_statistics['language-default-amount'] = language_default_amount
    for label, data in language_amounts.items():
        column_prefix = 'language-' + label
        language_amount_column = column_prefix + '-amount'
    
        collected_statistics[language_amount_column] = data['amount']

        if batch_mode:
            format_confidence_column = column_prefix + '-confidence'
            collected_statistics[format_confidence_column] = data['confidence'] 
        else:
            label_confidence = data['confidence']             
            confidence_min_column = column_prefix + '-confidence-min'
            confidence_min = 0
            confidence_max_column = column_prefix + '-confidence-max'
            confidence_max = 0
            confidence_mean_column = column_prefix + '-confidence-mean'
            confidence_mean = 0
            confidence_median_column = column_prefix + '-confidence-median'
            confidence_median = 0
            if 0 < len(label_confidence):
                confidence_min = min(label_confidence)
                confidence_max = max(label_confidence)
                confidence_mean = statistics.mean(label_confidence)
                confidence_median = statistics.median(label_confidence)
            
            collected_statistics[confidence_min_column] = confidence_min
            collected_statistics[confidence_max_column] = confidence_max
            collected_statistics[confidence_mean_column] = confidence_mean
            collected_statistics[confidence_median_column] = confidence_median
    return collected_statistics

def fasttext_get_languages(
    model: any,
    texts: list,
    default_value: str,
    default_threshold: str,
    label_replacer: any
):
    detected_languages = []
    language_default_amount = 0
    for content in texts:
        cleaned_text = content.replace('\n', ' ')
        
        labels, confidences = model.predict(cleaned_text, k=1)  
        language_label = labels[0].replace('__label__', '')
        label_confidence = float(confidences[0])

        if 0 < len(label_replacer):
            if language_label in label_replacer:
                language_label = label_replacer[language_label]

        if not language_label == default_value:
            if label_confidence < default_threshold:
                language_label = default_value
                label_confidence = 0.0
                language_default_amount += 1
        
        detected_languages.append((language_label, label_confidence))
    
    return detected_languages, language_default_amount