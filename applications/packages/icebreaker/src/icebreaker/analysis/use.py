
def analysis_internal_dataset_stats(
    dataset_df: any
):
    try: 
        import time as t
        from ..analysis.utility import analysis_pandas_format, analysis_pandas_material, analysis_pandas_paths
    except ImportError as e:
        raise ImportError("analysis/use failed to import", e)
 
    internal_statistics = {}
    
    format_replacer = {
        'py': 'python',
        'sh': 'bash',
        'md': 'markdown',
        'ipynb': 'jupyter',
        'txt': 'text',
        'png': 'image'
    }
    
    # format-(type)-count
    analysis_pandas_format(
        df = dataset_df,
        target_column = 'absolute-path',
        format_replacer = format_replacer,
        column_prefix = 'format',
        collected_statistics = internal_statistics
    )
    
    # material-(method)
    analysis_pandas_material(
        df = dataset_df,
        group_column = 'chapter',
        target_column = 'ref-material',
        column_prefix = 'material',
        collected_statistics = internal_statistics
    )
    # paths-(method)
    analysis_pandas_paths(
        df = dataset_df,
        group_column = 'chapter',
        target_column = 'ref-paths',
        format_replacer = format_replacer,
        column_prefix = 'paths',
        collected_statistics = internal_statistics
    )
    
    return internal_statistics

def analysis_internal_data_analysis(
    swift_client: any,
    run_parameters: dict,
    dataset_paths: list,
    storage_parameters: dict,
    group_columns: list,
    target_columns: list
):
    try: 
        import pandas as pd
        from ..objects.use import objects_get_data
    except ImportError as e:
        raise ImportError("workflow/use failed to import", e)

    df_list = []
    formatted_metrics = {}
    dataset_names = {}
    for dataset_path in dataset_paths:
        data_object = objects_get_data(
            swift_client = swift_client,
            storage_parameters = {
                'bucket-target': storage_parameters['bucket-target'],
                'bucket-prefix': storage_parameters['bucket-prefix'],
                'bucket-user': storage_parameters['bucket-user'],
                'object-name': 'root',
                'object-serialization': storage_parameters['object-serialization'],
                'path-replacers': {
                    'name': dataset_path
                },
                'path-names': [],
                'debug-prints': True,
                'lock-parameters': {},
                'lock-location': None,
                'overwrite': True
            },
            dict_format = False
        ) 

        object_df = data_object[0]
        #dataset_name = dataset_path.split('/')[-1].split('.')[0].split('-')[-1]
        dataset_name = dataset_path.split('/')[-1].split('.')[0]
        dataset_key = dataset_name.split('-')[-1]
        dataset_names[str(dataset_key)] = dataset_name

        formatted_metrics[dataset_name] = analysis_internal_dataset_stats(
            dataset_df = object_df
        )

        df_list.append(data_object[0])

    unified_tutorial_df = pd.concat(df_list, ignore_index = True)
    wanted_stats = [
        'size',
        'mean', 
        'std', 
        'median', 
        'min', 
        'max'
    ]
    for single_group in group_columns:
        df_stats = unified_tutorial_df.groupby(single_group)[target_columns].agg(wanted_stats).to_dict()
        for tuple, values in df_stats.items():
            for group_case, stat_value in values.items():
                flattened_key = f'{tuple[0]}-{tuple[1]}'
                dataset_name = dataset_names[str(group_case)]
                formatted_metrics[dataset_name][flattened_key] = stat_value
    
    df_group_stats = unified_tutorial_df.groupby(group_columns)[target_columns].agg(wanted_stats).to_dict()
    for tuple, values in df_group_stats.items():
        for group_tuple, stat_value in values.items():
            flattened_key = f'{tuple[0]}-{group_columns[1]}-{group_tuple[1]}-{tuple[1]}'
            dataset_name = dataset_names[str(group_tuple[0])]
            formatted_metrics[dataset_name][flattened_key] = stat_value

    return {
        'parameters': run_parameters,
        'metrics': formatted_metrics
    }
'''
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
'''
