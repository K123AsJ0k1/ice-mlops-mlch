
def analysis_internal_statistics(
    model_path: str,
    internal_data_dfs: any,
    analysis_parameters: any
): 
    try:
        import time as t
        import fasttext
        from ..pd_stats.use import (
            stats_pandas_max, 
            stats_pandas_groupby_max,
            stats_pandas_basic, 
            stats_pandas_format, 
            stats_pandas_material, 
            stats_pandas_paths, 
        )
        from ..fast_text.use import fasttext_get_stats
    except ImportError as e:
        raise ImportError("Failed to import", e)

    start_time = t.time()
    fasttest_model = fasttext.load_model(model_path)
    internal_statistics = {}
    index = 1

    language_default = analysis_parameters['language-default']
    language_column = analysis_parameters['language-column']
    language_threshold = analysis_parameters['language-threshold']
    language_replacer = analysis_parameters['language-replacer']
    
    format_column = analysis_parameters['format-column']
    format_replacer = analysis_parameters['format-replacer']

    for part_df in internal_data_dfs:
        key_name = 'part-' + str(index)
        internal_statistics[key_name] = {}
        # index
        internal_statistics[key_name]['index'] = index
        # amount
        amount = part_df.shape[0]
        internal_statistics[key_name]['amount'] = amount
        # chapters
        stats_pandas_max(
            df = part_df, 
            column = 'chapter', 
            collection_key = key_name,
            stat_key = 'chapters',
            collected_statistics = internal_statistics
        )
        # chapter-index-(key)
        stats_pandas_groupby_max(
            df = part_df,
            group_column = 'chapter',
            target_column = 'index',
            collection_key = key_name,
            column_prefix = 'chapter',
            collected_statistics = internal_statistics
        )
        # documents
        stats_pandas_max(
            df = part_df, 
            column = 'document', 
            collection_key = key_name,
            stat_key = 'documents',
            collected_statistics = internal_statistics
        )
        # Speaking language-(type)
        language_stats = fasttext_get_stats(
            model = fasttest_model,
            texts = part_df[language_column],
            default_value = language_default,
            default_threshold = language_threshold,
            label_replacer = language_replacer
        )

        for stat_name, value in language_stats.items():
            internal_statistics[key_name][stat_name] = value
        # format-(type)-count
        stats_pandas_format(
            df = part_df,
            target_column = format_column,
            format_replacer = format_replacer,
            collection_key = key_name,
            column_prefix = 'format',
            collected_statistics = internal_statistics
        )
        # row-(method)
        stats_pandas_basic(
            df = part_df,
            column = 'rows',
            collection_key = key_name,
            collected_statistics = internal_statistics
        )
        # characters-(method)
        stats_pandas_basic(
            df = part_df,
            column = 'characters',
            collection_key = key_name,
            collected_statistics = internal_statistics
        )
        # material-(method)
        stats_pandas_material(
            df = part_df,
            group_column = 'chapter',
            target_column = 'ref-material',
            collection_key = key_name,
            column_prefix = 'material',
            collected_statistics = internal_statistics
        )
        # paths-(method)
        stats_pandas_paths(
            df = part_df,
            group_column = 'chapter',
            target_column = 'ref-paths',
            format_replacer = format_replacer,
            collection_key = key_name,
            column_prefix = 'paths',
            collected_statistics = internal_statistics
        )
        
        index += 1

    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return internal_statistics

def analysis_external_statistics(
    model_path: str,
    external_data_df: any,
    analysis_parameters: any
):
    try:
        import time as t
        import fasttext
        from ..pd_stats.use import (
            stats_pandas_amount, 
            stats_pandas_max, 
            stats_pandas_groupby_max,
            stats_pandas_basic, 
            stats_pandas_format, 
            stats_pandas_material, 
            stats_pandas_paths, 
            stats_pandas_content
        )
        from ..mgka.use import  magika_get_stats
        from ..fast_text.use import fasttext_get_stats
        from magika import Magika, PredictionMode
    except ImportError as e:
        raise ImportError("Failed to import", e)

    start_time = t.time()
    fasttext_model = fasttext.load_model(model_path)
    magika_model = Magika(prediction_mode = PredictionMode.MEDIUM_CONFIDENCE)
    external_statistics = {}
    
    #dataset_type = analysis_parameters['dataset-type']

    language_default = analysis_parameters['language-default']
    language_column = analysis_parameters['language-column']
    language_threshold = analysis_parameters['language-threshold']
    language_replacer = analysis_parameters['language-replacer']
    
    format_default = analysis_parameters['format-default']
    format_column = analysis_parameters['format-column']
    format_threshold = analysis_parameters['format-threshold']
    format_replacer = analysis_parameters['format-replacer']

    amount = external_data_df.shape[0]
    external_statistics['amount'] = amount

    # question-(type)-(method)
    stats_pandas_content(
        df = external_data_df,
        target_column = 'question',
        column_prefix = 'question',
        collected_statistics = external_statistics
    )
    # answer-(type)-(method)
    stats_pandas_content(
        df = external_data_df,
        target_column = 'answer',
        column_prefix = 'answer',
        collected_statistics = external_statistics
    )
    # language-(type)-(method)
    language_stats = fasttext_get_stats(
        model = fasttext_model,
        texts = external_data_df[language_column],
        default_value = language_default,
        default_threshold = language_threshold,
        label_replacer = language_replacer
    )
    for stat_name, value in language_stats.items():
        external_statistics[stat_name] = value
    # format-(type)-amount
    format_stats = magika_get_stats(
        model = magika_model,
        texts = external_data_df[format_column],
        default_value = format_default,
        default_threshold = format_threshold,
        label_replacer = format_replacer
    )
    for stat_name, value in format_stats.items():
        external_statistics[stat_name] = value

    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return external_statistics