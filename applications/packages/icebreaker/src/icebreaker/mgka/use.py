
def magika_get_stats(
    model: any,
    texts: any,
    default_value: str,
    default_threshold: str,
    label_replacer: any
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

        prediction =  model.identify_bytes(formatted_text)
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
                'confidences': confidence_starting_value
            }
        else:
            format_amounts[format_label]['amount'] += 1
            if not label_confidence == 0.0:
                format_amounts[format_label]['confidences'].append(label_confidence)
        
    for label, data in format_amounts.items():
        column_prefix = 'format-' + label
        format_amount_column = column_prefix + '-amount'
    
        label_amount = data['amount']
        label_confidences = data['confidences']             

        confidence_min_column = column_prefix + '-confidence-min'
        confidence_min = 0
        confidence_max_column = column_prefix + '-confidence-max'
        confidence_max = 0
        confidence_mean_column = column_prefix + '-confidence-mean'
        confidence_mean = 0
        confidence_median_column = column_prefix + '-confidence-median'
        confidence_median = 0
        if 0 < len(label_confidences):
            confidence_min = min(label_confidences)
            confidence_max = max(label_confidences)
            confidence_mean = statistics.mean(label_confidences)
            confidence_median = statistics.median(label_confidences)
        
        collected_statistics[format_amount_column] = label_amount
        collected_statistics[confidence_min_column] = confidence_min
        collected_statistics[confidence_max_column] = confidence_max
        collected_statistics[confidence_mean_column] = confidence_mean
        collected_statistics[confidence_median_column] = confidence_median
    collected_statistics['format-default-amount'] = format_default_amount
    return collected_statistics