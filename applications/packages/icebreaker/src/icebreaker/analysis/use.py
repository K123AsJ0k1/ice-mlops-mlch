
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
    storage_parameters: dict
):
    try: 
        import pandas as pd
        from ..objects.use import objects_get_data
    except ImportError as e:
        raise ImportError("workflow/use failed to import", e)

    df_list = []
    formatted_metrics = {}
    collected_tables = {}
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
        dataset_name = dataset_path.split('/')[-1].split('.')[0]
        dataset_key = dataset_name.split('-')[-1]
        dataset_names[str(dataset_key)] = dataset_name

        formatted_metrics[dataset_name] = analysis_internal_dataset_stats(
            dataset_df = object_df
        )

        collected_tables[dataset_name] = object_df

        df_list.append(object_df)

    unified_tutorial_df = pd.concat(df_list, ignore_index = True)

    group_columns = [
        'part',
        'relevance'
    ]

    target_columns =[
        'rows',
        'characters'
    ]
    
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
        'metrics': formatted_metrics,
        'tables': collected_tables
    }

def analysis_external_dataset_stats(
    dataset_df: any,
    language_default: str,
    format_default: str
):
    try: 
        import time as t
        from ..analysis.utility import analysis_pandas_content
    except ImportError as e:
        raise ImportError("analysis/use failed to import", e)

    internal_statistics = {}

    question_results = analysis_pandas_content( 
        df = dataset_df,
        target_column = 'question',
        collected_statistics = internal_statistics
    )

    answer_results = analysis_pandas_content(
        df = dataset_df,
        target_column = 'answer',
        collected_statistics = internal_statistics
    )

    language_column = f'language-{language_default}-size'
    format_column = f'format-{format_default}-size'

    internal_statistics[language_column] = dataset_df.shape[0]
    internal_statistics[format_column] = dataset_df.shape[0]

    return {
        'stats':internal_statistics,
        'question-results': question_results,
        'answer-results': answer_results
    }

def analysis_external_data_analysis(
    swift_client: any,
    run_parameters: dict,
    dataset_paths: list,
    storage_parameters: dict,
    dataset_defaults: dict
):
    try: 
        import pandas as pd
        from ..objects.use import objects_get_data
    except ImportError as e:
        raise ImportError("workflow/use failed to import", e)

    df_list = []
    formatted_metrics = {
        'external-general': {}
    }
    collected_tables = {}

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
        dataset_name = dataset_path.split('/')[-1].split('.')[0]

        analysis_results = analysis_external_dataset_stats(
            dataset_df = object_df,
            language_default = dataset_defaults[dataset_name]['language-default'],
            format_default = dataset_defaults[dataset_name]['format-default']
        )

        formatted_metrics[dataset_name] = analysis_results['stats']

        object_df['dataset'] = dataset_name
        object_df['question-rows'] = analysis_results['question-results']['rows']
        object_df['question-characters'] = analysis_results['question-results']['chars']
        object_df['answer-rows'] = analysis_results['answer-results']['rows']
        object_df['answer-characters'] = analysis_results['answer-results']['chars']

        collected_tables[dataset_name] = object_df
        df_list.append(object_df)
        
    unified_tutorial_df = pd.concat(df_list, ignore_index = True)

    target_columns =[
        'question-rows',
        'question-characters',
        'answer-rows',
        'answer-characters'
    ]
    
    wanted_stats = [
        'size',
        'mean', 
        'std', 
        'median', 
        'min', 
        'max'
    ]
    
    df_stats = unified_tutorial_df[target_columns].agg(wanted_stats).to_dict()
    for name, values in df_stats.items():
        for key, value in values.items():
            flattened_key = f'{name}-{key}'
            formatted_metrics['external-general'][flattened_key] = value
        
    return {
        'parameters': run_parameters,
        'metrics': formatted_metrics,
        'tables': collected_tables
    }
