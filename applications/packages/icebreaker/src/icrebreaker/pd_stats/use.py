
def stats_pandas_amount(
    df: any,
    collection_key: str,
    stat_key: str,
    collected_statistics: any
):
    amount = df.shape[0]
    collected_statistics[collection_key][stat_key] = amount

def stats_pandas_max(
    df: any,
    column: str,
    collection_key: str,
    stat_key: str,
    collected_statistics: any
) -> int:
    max_value = int(df[column].max())
    collected_statistics[collection_key][stat_key] = max_value

def stats_pandas_groupby_max(
    df: any,
    group_column: str,
    target_column: str,
    collection_key: str,
    column_prefix: str,
    collected_statistics: any
):
    group_targets = df.groupby(group_column)[target_column].max()
    for key, value in group_targets.items():
        if key == 0:
            continue
        column_name = column_prefix + '-' + str(key) + '-max-index'
        collected_statistics[collection_key][column_name] = value

def stats_pandas_basic(
    df: any,
    column: str,
    collection_key: str,
    collected_statistics: any
):
    min_name = column + '-mix'
    max_name = column + '-max'
    mean_name = column + '-mean'
    median_name = column + '-median'
    
    min_value = int(df[column].min())
    mean_value = float(df[column].mean())
    median_value = float(df[column].median())

    collected_statistics[collection_key][min_name] = min_value
    stats_pandas_max(
        df = df, 
        column = column, 
        collection_key = collection_key,
        stat_key = max_name,
        collected_statistics = collected_statistics
    ) 
    collected_statistics[collection_key][mean_name] = mean_value
    collected_statistics[collection_key][median_name] = median_value

def stats_pandas_format(
    df: any,
    target_column: str,
    format_replacer: any,
    collection_key: str,
    column_prefix: str,
    collected_statistics: any
):
    try:
        from pathlib import Path
    except ImportError as e:
        raise ImportError("Failed to import", e)

    format_counts = df[target_column].apply(lambda x: Path(x).suffix.lower()).value_counts()
    for key, value in format_counts.items():
        format_name = str(key.split('.')[1])

        if 0 < len(format_replacer):
            if format_name in format_replacer:
                format_name = format_replacer[format_name]

        column_name = column_prefix + '-' + format_name + '-amount'
        collected_statistics[collection_key][column_name] = value

def stats_pandas_material(
    df: any,
    group_column: str,
    target_column: str,
    collection_key: str,
    column_prefix: str,
    collected_statistics: any
):
    try:
        import statistics
    except ImportError as e:
        raise ImportError("Failed to import", e)

    group_targets = df.groupby(group_column)[target_column].first()
    target_amounts = []
    for chapter_key, values in group_targets.items():
        if chapter_key == 0:
            continue
        ref_amount = 0
        for ref_key in values.keys():
            if 'url' in ref_key:
                ref_amount += 1

        target_amounts.append(ref_amount)
        column_name = column_prefix + '-chapter-' + str(chapter_key) + '-amount'
        collected_statistics[collection_key][column_name] = ref_amount
    
    amount_name = column_prefix + '-amount'
    min_name = column_prefix + '-mix'
    max_name = column_prefix + '-max'
    mean_name = column_prefix + '-mean'
    median_name = column_prefix + '-median'
    
    target_amount = sum(target_amounts)
    target_min = min(target_amounts)
    target_max = max(target_amounts)
    target_mean = statistics.mean(target_amounts)
    target_median = statistics.median(target_amounts)

    collected_statistics[collection_key][amount_name] = target_amount
    collected_statistics[collection_key][min_name] = target_min
    collected_statistics[collection_key][max_name] = target_max
    collected_statistics[collection_key][mean_name] = target_mean
    collected_statistics[collection_key][median_name] = target_median

def stats_pandas_paths(
    df: any,
    group_column: str,
    target_column: str,
    format_replacer: any,
    collection_key: str,
    column_prefix: str,
    collected_statistics: any
):
    try:
        import statistics
    except ImportError as e:
        raise ImportError("Failed to import", e)

    ref_formats = {}
    ref_chapter_amounts = {}
    for chapter, paths in zip(df[group_column], df[target_column]):
        if chapter == 0:
            continue
        
        for relative, absolute in paths.items():
            file_format = absolute.split('/')[-1].split('.')[-1]
            if not file_format in ref_formats:
                ref_formats[file_format] = 1
            else:
                ref_formats[file_format] = ref_formats[file_format] + 1
        
        if not chapter in ref_chapter_amounts:
            ref_chapter_amounts[chapter] = len(paths)
        else:
            ref_chapter_amounts[chapter] = ref_chapter_amounts[chapter] + len(paths)

    for format, amount in ref_formats.items():
        format_name = str(format)
        if 0 < len(format_replacer):
            if format_name in format_replacer:
                format_name = format_replacer[format_name]

        column_name = column_prefix + '-format-' + format_name + '-amount'
        collected_statistics[collection_key][column_name] = amount
        
    ref_amounts = []
    for chapter, amount in ref_chapter_amounts.items():
        column_name = column_prefix + '-chapter-' + str(chapter) + '-amount'
        collected_statistics[collection_key][column_name] = amount
        ref_amounts.append(amount)

    amount_name = column_prefix + '-amount'
    min_name = column_prefix + '-mix'
    max_name = column_prefix + '-max'
    mean_name = column_prefix + '-mean'
    median_name = column_prefix + '-median'

    target_amount = sum(ref_amounts)
    target_min = min(ref_amounts)
    target_max = max(ref_amounts)
    target_mean = statistics.mean(ref_amounts)
    target_median = statistics.median(ref_amounts)

    collected_statistics[collection_key][amount_name] = target_amount
    collected_statistics[collection_key][min_name] = target_min
    collected_statistics[collection_key][max_name] = target_max 
    collected_statistics[collection_key][mean_name] = target_mean
    collected_statistics[collection_key][median_name] = target_median

def stats_pandas_content(
    df: any,
    target_column: str,
    column_prefix: str,
    collected_statistics: any
):
    try:
        import statistics
    except ImportError as e:
        raise ImportError("Failed to import", e)

    rows = []
    chars = []
    for content in df[target_column]:
        content_rows = len(content.splitlines())
        content_chars = len(content)
        rows.append(content_rows)
        chars.append(content_chars)
        
    min_rows_name = column_prefix + '-rows-mix'
    max_rows_name = column_prefix + '-rows-max'
    mean_rows_name = column_prefix + '-rows-mean'
    median_rows_name = column_prefix + '-rows-median'

    rows_min = min(rows)
    rows_max = max(rows)
    rows_mean = statistics.mean(rows)
    rows_median = statistics.median(rows)

    collected_statistics[min_rows_name] = rows_min
    collected_statistics[max_rows_name] = rows_max
    collected_statistics[mean_rows_name] = rows_mean
    collected_statistics[median_rows_name] = rows_median

    min_chars_name = column_prefix + '-characters-mix'
    max_chars_name = column_prefix + '-characters-max'
    mean_chars_name = column_prefix + '-characters-mean'
    median_chars_name = column_prefix + '-characters-median'

    chars_min = min(chars)
    chars_max = max(chars)
    chars_mean = statistics.mean(chars)
    chars_median = statistics.median(chars)

    collected_statistics[min_chars_name] = chars_min
    collected_statistics[max_chars_name] = chars_max
    collected_statistics[mean_chars_name] = chars_mean
    collected_statistics[median_chars_name] = chars_median