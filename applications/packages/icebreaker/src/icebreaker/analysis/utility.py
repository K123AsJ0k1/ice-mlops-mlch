
'''
def analysis_pandas_amount(
    df: any,
    collection_key: str,
    stat_key: str,
    collected_statistics: any
):
    amount = df.shape[0]
    collected_statistics[collection_key][stat_key] = amount

def analysis_pandas_max(
    df: any,
    column: str,
    collection_key: str,
    stat_key: str,
    collected_statistics: any
) -> int:
    max_value = int(df[column].max())
    collected_statistics[collection_key][stat_key] = max_value

def analysis_pandas_groupby_max(
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

def analysis_pandas_basic(
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
'''
def analysis_pandas_format(
    df: any,
    target_column: str,
    format_replacer: any,
    column_prefix: str,
    collected_statistics: any
):
    try:
        from pathlib import Path
    except ImportError as e:
        raise ImportError("analysis/utility failed to import", e)

    format_counts = df[target_column].apply(lambda x: Path(x).suffix.lower()).value_counts()
    for key, value in format_counts.items():
        format_name = str(key.split('.')[1])

        if 0 < len(format_replacer):
            if format_name in format_replacer:
                format_name = format_replacer[format_name]

        column_name = column_prefix + '-' + format_name + '-size'
        collected_statistics[column_name] = value

def analysis_pandas_material(
    df: any,
    group_column: str,
    target_column: str,
    column_prefix: str,
    collected_statistics: any
):
    try:
        import statistics
    except ImportError as e:
        raise ImportError("analysis/utility failed to import", e)
    
    target_amounts = []
    chapter_wide_amounts = {}
    for chapter, material in zip(df[group_column], df[target_column]):
        if chapter == 0:
            continue
    
        ref_amount = 0
        for ref_key in material.keys():
            if 'url' in ref_key:
                ref_amount += 1

        if not chapter in chapter_wide_amounts:
            chapter_wide_amounts[chapter] = ref_amount
        else:
            chapter_wide_amounts[chapter] += ref_amount
        
        target_amounts.append(ref_amount)

    for chapter, refs in chapter_wide_amounts.items():
        column_name = f'{column_prefix}-chapter-{chapter}-size'
        collected_statistics[column_name] = refs
    
    amount_name = column_prefix + '-size'
    min_name = column_prefix + '-mix'
    max_name = column_prefix + '-max'
    mean_name = column_prefix + '-mean'
    median_name = column_prefix + '-median'
    std_name = column_prefix + '-std'
    
    target_amount = sum(target_amounts)
    target_min = min(target_amounts)
    target_max = max(target_amounts)
    target_mean = statistics.mean(target_amounts)
    target_median = statistics.median(target_amounts)
    target_std = statistics.stdev(target_amounts)

    collected_statistics[amount_name] = target_amount
    collected_statistics[min_name] = target_min
    collected_statistics[max_name] = target_max
    collected_statistics[mean_name] = target_mean
    collected_statistics[median_name] = target_median
    collected_statistics[std_name] = target_std

def analysis_pandas_paths(
    df: any,
    group_column: str,
    target_column: str,
    format_replacer: any,
    column_prefix: str,
    collected_statistics: any
):
    try:
        import statistics
    except ImportError as e:
        raise ImportError("analysis/utility failed to import", e)

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
        collected_statistics[column_name] = amount
        
    ref_amounts = []
    for chapter, amount in ref_chapter_amounts.items():
        column_name = column_prefix + '-chapter-' + str(chapter) + '-amount'
        collected_statistics[column_name] = amount
        ref_amounts.append(amount)

    amount_name = column_prefix + '-amount'
    min_name = column_prefix + '-mix'
    max_name = column_prefix + '-max'
    mean_name = column_prefix + '-mean'
    median_name = column_prefix + '-median'
    std_name = column_prefix + '-std'

    target_amount = sum(ref_amounts)
    target_min = min(ref_amounts)
    target_max = max(ref_amounts)
    target_mean = statistics.mean(ref_amounts)
    target_median = statistics.median(ref_amounts)
    target_std = statistics.stdev(ref_amounts)

    collected_statistics[amount_name] = target_amount
    collected_statistics[min_name] = target_min
    collected_statistics[max_name] = target_max 
    collected_statistics[mean_name] = target_mean
    collected_statistics[median_name] = target_median
    collected_statistics[std_name] = target_std
