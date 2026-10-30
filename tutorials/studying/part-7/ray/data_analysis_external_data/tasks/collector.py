import ray
import time as t
import pandas as pd
from icebreaker.swift.setup import swift_setup_client
from icebreaker.objects.use import objects_get_data
from icebreaker.analysis.utility import analysis_get_rows_chars
from icebreaker.objects.use import objects_store_data, objects_get_prefix_list
from icebreaker.storage.management import storage_set_object_path

@ray.remote( 
    num_cpus = 1,
    memory = 0.4 * 1024 * 1024 * 1024
) 
def data_collector(
    worker_index: int,
    actor_index: int,
    actor_ref: any,
    swift_parameters: dict,
    input_storage_parameters: dict,
    config_parameters: dict,
    task_batch: list,
    output_storage_parameters: dict,
    log_parameters: dict
) -> any:
    start_time = t.time()
    print(f'Task {worker_index}, Actor {actor_index}')
    
    print('Setting up swift client')
    # If you expect the task to last over 8 hours, consider renewal
    swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )
    print('Swift client setup') 

    analysis_parameters = config_parameters['analysis-parameters']
    
    language_column = 'question'   
    format_column = 'answer'
    
    formatted_metrics = {}
    original_tables = {}
    analysis_results = {}
    provider_actor_refs = []
    batch_index = 1
    for batch_data in task_batch:
        object_path = batch_data[0]
        key_name = object_path.split('/')[-1].split('.')[0]

        if key_name not in formatted_metrics:
            formatted_metrics[key_name] = {}

        data_object = objects_get_data(
            swift_client = swift_client,
            storage_parameters = {
                'bucket-target': input_storage_parameters['bucket-target'],
                'bucket-prefix': input_storage_parameters['bucket-prefix'],
                'bucket-user': input_storage_parameters['bucket-user'],
                'object-name': 'root',
                'object-serialization': input_storage_parameters['object-serialization'],
                'path-replacers': {
                    'name': object_path
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
        original_tables[key_name] = object_df
        total_rows = object_df.shape[0]
        formatted_metrics[key_name]['dataset-size'] = total_rows

        # question-(type)-(method)
        question_results = analysis_get_rows_chars(
            df = object_df,
            target_column = language_column
        )
        # answer-(type)-(method)
        answer_results = analysis_get_rows_chars(
            df = object_df,
            target_column = format_column
        )

        analysis_results[key_name] = {
            'question-results': question_results,
            'answer-results': answer_results
        }

        chunk_size = 1000
        for i in range(0, total_rows, chunk_size):
            lang_chunk = object_df[language_column].iloc[i : i + chunk_size].tolist()
            format_chunk = object_df[format_column].iloc[i : i + chunk_size].tolist()

            # Speaking language-(type)
            # format-(type)-amount
            text_input_ref_1 = ray.put(lang_chunk)
            text_input_ref_2 = ray.put(format_chunk)
            provider_actor_refs.append(actor_ref.batch_get_stats.remote(
                worker_index = worker_index,
                actor_index = actor_index,
                batch_index = batch_index,
                used_key = key_name,
                language_text_input = text_input_ref_1,
                format_text_input = text_input_ref_2,
                analysis_parameters = analysis_parameters
            ))
            
        batch_index += 1 

    joined_tables_list = {}
    while len(provider_actor_refs):
        done_actor_refs, provider_actor_refs = ray.wait(provider_actor_refs)
        for output_ref in done_actor_refs: 
            result = ray.get(output_ref)
            batch_index = result['batch']
            key_name = result['key']
            
            language_table = result['language-data']['table']
            format_table = result['format-data']['table']

            merged_df = pd.concat([language_table, format_table], axis=1)

            if key_name not in joined_tables_list:
                joined_tables_list[key_name] = []

            joined_tables_list[key_name].append(merged_df)

    joined_tables = {}
    for key_name, dfs in joined_tables_list.items():
        joined_tables[key_name] = pd.concat(dfs, ignore_index=True)

    formatted_tables = {}
    for dataset_name, table in original_tables.items():
        question_results = analysis_results[dataset_name]['question-results']
        answer_results = analysis_results[dataset_name]['answer-results']
        formatted_table = table.copy()
        formatted_table['question-rows'] = question_results['rows']
        formatted_table['question-characters'] = question_results['chars']
        formatted_table['answer-rows'] = answer_results['rows']
        formatted_table['answer-characters'] = answer_results['chars']
        final_df = pd.concat(
            [formatted_table, joined_tables[dataset_name]],
            axis = 1
        )
        formatted_tables[dataset_name] = final_df
 
    number_columns = [
        'question-rows',
        'question-characters',
        'answer-rows',
        'answer-characters'
    ]

    language_columns = [
        'language',
        'language-confidence'
    ]

    format_columns = [
        'format',
        'format-confidence',
        'format-counts'
    ]

    wanted_stats = [
        'size',
        'mean', 
        'std', 
        'median', 
        'min', 
        'max'
    ]
    # join the tables
    for dataset_name, table in formatted_tables.items():
        df_number_stats = table[number_columns].agg(wanted_stats).to_dict()
        for name, values in df_number_stats.items():
            for key, value in values.items():
                flattened_key = f'{name}-{key}'
                formatted_metrics[dataset_name][flattened_key] = value

        df_language_stats = table.groupby(language_columns[0])[language_columns[1]].agg(wanted_stats).to_dict()
        for name, values in df_language_stats.items():
            for key, value in values.items():
                flattened_key = f'language-{key}-'
                if not 'size' == name:
                    flattened_key += 'confidence-'
                flattened_key += name

                formatted_metrics[dataset_name][flattened_key] = value

        df_format_stats = table.groupby(format_columns[0])[format_columns[1]].agg(wanted_stats).to_dict()
        for name, values in df_format_stats.items():
            for key, value in values.items():
                flattened_key = f'format-{key}-'
                if not 'size' == name:
                    flattened_key += 'confidence-'
                flattened_key += name
                formatted_metrics[dataset_name][flattened_key] = value

    name_start_prefix = output_storage_parameters['name-start-prefix']
    output_storage_parameters['debug-prints'] = True
    output_storage_parameters['lock-parameters'] = {}
    output_storage_parameters['lock-location'] = None
    output_storage_parameters['overwrite'] = True
    
    for dataset_name in formatted_metrics.keys():
        metrics = formatted_metrics[dataset_name]
        table = formatted_tables[dataset_name]
        used_identity = dataset_name.split('external')[1][1:]

        artifact = {
            'parameters': log_parameters,
            'metrics': metrics
        }

        artifact_object_name = 'arti'
        artifact_path_replacers = {
            'name': 'METRICS'
        }

        artifact_path_name = f'{name_start_prefix}-metrics-{used_identity}-'

        artifact_temp_path_names = [
            artifact_path_name
        ]

        artifact_path = storage_set_object_path(
            object_name = artifact_object_name,
            path_replacers = artifact_path_replacers,
            path_names = artifact_temp_path_names,
            debug_prints = False
        )

        object_list = objects_get_prefix_list(
            storage_client = swift_client,
            storage_parameters = output_storage_parameters,
            path_prefix = artifact_path
        )

        next_index = len(object_list) + 1
        
        artifact_path_name += f'run-{next_index}.pkl'
        
        output_storage_parameters['object-name'] = artifact_object_name
        output_storage_parameters['object-serialization'] = 'pickle'
        output_storage_parameters['path-replacers'] = artifact_path_replacers
        output_storage_parameters['path-names'] = [
            artifact_path_name
        ]
        output_storage_parameters['debug-prints'] = True
        output_storage_parameters['lock-parameters'] = {}
        output_storage_parameters['lock-location'] = None
        output_storage_parameters['overwrite'] = True
        
        artifact_stored = objects_store_data(
            swift_client = swift_client,
            storage_parameters = output_storage_parameters,
            object_data = artifact,
            object_metadata = {}
        )
        
        table_path_name = f'{name_start_prefix}-data-{dataset_name}.parquet'
        
        output_storage_parameters['object-name'] = 'data'
        output_storage_parameters['object-serialization'] = 'parquet'
        output_storage_parameters['path-replacers'] = {
            'name': 'EXTRACTED'
        }
        output_storage_parameters['path-names'] = [
            table_path_name
        ]
        output_storage_parameters['debug-prints'] = True
        output_storage_parameters['lock-parameters'] = {}
        output_storage_parameters['lock-location'] = None
        output_storage_parameters['overwrite'] = True
        
        table_stored = objects_store_data(
            swift_client = swift_client,
            storage_parameters = output_storage_parameters,
            object_data = table,
            object_metadata = {}
        )
        
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return {
        'metrics': formatted_metrics
    }