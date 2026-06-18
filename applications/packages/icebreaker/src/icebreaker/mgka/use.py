
def magika_get_stats(
    model: any,
    texts: any,
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
    format_amounts = {}
    format_default_amount = 0
    for content in texts:
        formatted_text = content.encode('utf-8')

        prediction = model.identify_bytes(formatted_text)
        format_label = prediction.output.label
        label_confidence = prediction.score

        if 0 < len(label_replacer):
            if format_label in label_replacer:
                format_label = label_replacer[format_label]
        
        if not format_label == default_value:
            if label_confidence < default_threshold:
                format_label = default_value
                label_confidence = 0.0
                format_default_amount += 1
        
        if not format_label in format_amounts:
            confidence_starting_value = []
            if not label_confidence == 0.0:
                confidence_starting_value.append(label_confidence)
            format_amounts[format_label] = {
                'amount': 1,
                'confidence': confidence_starting_value
            }
        else:
            format_amounts[format_label]['amount'] += 1
            if not label_confidence == 0.0:
                format_amounts[format_label]['confidence'].append(label_confidence)
    collected_statistics['format-default-amount'] = format_default_amount
    for label, data in format_amounts.items():
        column_prefix = 'format-' + label
        format_amount_column = column_prefix + '-amount'
    
        collected_statistics[format_amount_column] = data['amount']

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

def magika_get_formats(
    model: any,
    texts: any,
    default_value: str,
    default_threshold: str,
    label_replacer: any
): 
    detected_formats = []
    format_default_amount = 0
    for content in texts:
        formatted_text = content.encode('utf-8')

        prediction = model.identify_bytes(formatted_text)
        format_label = prediction.output.label
        label_confidence = prediction.score

        if 0 < len(label_replacer):
            if format_label in label_replacer:
                format_label = label_replacer[format_label]
        
        if not format_label == default_value:
            if label_confidence < default_threshold:
                format_label = default_value
                label_confidence = 0.0
                format_default_amount += 1
        
        detected_formats.append((format_label, label_confidence))
    
    return detected_formats, format_default_amount
