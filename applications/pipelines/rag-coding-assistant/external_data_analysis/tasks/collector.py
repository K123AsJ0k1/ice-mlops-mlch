import ray
import statistics
import time as t
from icebreaker.swift.setup import swift_setup_client, swift_renew_client
from icebreaker.storage.management import object_storage_interaction
from icebreaker.pd_stats.use import (
    stats_pandas_content
)
from icebreaker.pyarrow.use import pyarrow_deserialize_dataframe

@ray.remote(
    num_cpus = 1,
    memory = 0.2 * 1024 * 1024 * 1024
) 
def data_collector(
    worker_index: int,
    actor_index: int,
    actor_ref: any,
    swift_parameters: any,
    data_storage_parameters: any,
    config_parameters: any,
    task_batch: any
) -> any:
    start_time = t.time()
    print('Task', worker_index, 'Actor', actor_index)
    
    print('Setting up swift client')
    # If you expect the task to last over 8 hours, consider renewal
    setup_swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )
    print('Swift client setup') 

    analysis_parameters = config_parameters['analysis-parameters']
    
    language_column = analysis_parameters['language-column']    
    format_column = analysis_parameters['format-column']
    
    collected_stats = {}
    list_stats = {}
    provider_actor_refs = []
    batch_index = 1
    for batch_data in task_batch:
        print('Swift client renew check')
        swift_client = swift_renew_client(
            secret_parameters = swift_parameters,
            swift_client = swift_client
        )

        object_path = batch_data[0]
        key_name = object_path.split('/')[-1].split('.')[0]

        if key_name not in collected_stats:
            collected_stats[key_name] = {}
            list_stats[key_name] = {}

        stored_dataset = object_storage_interaction(
            storage_client = setup_swift_client,
            parameters = {
                'mode': 'get',
                'bucket-target': data_storage_parameters['bucket-target'],
                'bucket-prefix': data_storage_parameters['bucket-prefix'],
                'bucket-user': data_storage_parameters['bucket-user'],
                'debug-prints': True,
                'object-name': 'root',
                'path-replacers': {
                    'name': object_path
                },
                'path-names': [],
                'overwrite': True,
                'lock-parameters': {},
                'lock-location': ''
            },
            object_data = None,
            object_metadata = None
        )  
        pandas_df = pyarrow_deserialize_dataframe(serialized_dataframe = stored_dataset[0])

        amount = pandas_df.shape[0]
        collected_stats[key_name]['amount'] = amount

        # question-(type)-(method)
        stats_pandas_content(
            df = pandas_df,
            target_column = 'question',
            column_prefix = 'question',
            collected_statistics = collected_stats[key_name]
        )
        # answer-(type)-(method)
        stats_pandas_content(
            df = pandas_df,
            target_column = 'answer',
            column_prefix = 'answer',
            collected_statistics = collected_stats[key_name]
        )

        chunk_size = 1000
        total_rows = len(pandas_df)
        for i in range(0, total_rows, chunk_size):
            lang_chunk = pandas_df[language_column].iloc[i : i + chunk_size].tolist()
            format_chunk = pandas_df[format_column].iloc[i : i + chunk_size].tolist()

            # Speaking language-(type)
            text_input_ref_1 = ray.put(lang_chunk)
            provider_actor_refs.append(actor_ref.batch_fasttext_stats.remote(
                worker_index = worker_index,
                actor_index = actor_index,
                batch_index = batch_index,
                used_key = key_name,
                text_input = text_input_ref_1,
                analysis_parameters = analysis_parameters
            ))
            # format-(type)-amount
            text_input_ref_2 = ray.put(format_chunk)
            provider_actor_refs.append(actor_ref.batch_magika_stats.remote(
                worker_index = worker_index,
                actor_index = actor_index,
                batch_index = batch_index,
                used_key = key_name,
                text_input = text_input_ref_2,
                analysis_parameters = analysis_parameters
            ))
        
        batch_index += 1
    
    while len(provider_actor_refs):
        done_actor_refs, provider_actor_refs = ray.wait(provider_actor_refs)
        for output_ref in done_actor_refs: 
            result = ray.get(output_ref)
            batch_index = result['batch']
            stats = result['stats']
            key_name = result['key']
            
            for stat_name, value in stats.items():
                if isinstance(value, (int, float)):
                    if stat_name in collected_stats[key_name]:
                        collected_stats[key_name][stat_name] += value
                    else:
                        collected_stats[key_name][stat_name] = value
                if isinstance(value, list):
                    if stat_name in collected_stats[key_name]:
                        list_stats[key_name][stat_name].extend(value)
                    else:
                        list_stats[key_name][stat_name] = value
    
    for key_name, stat_values in list_stats.items():
        for stat_name, list_value in stat_values.items():
            if 'confidence' in stat_name:
                confidence_min_column = key_name + '-' + stat_name + '-min'
                confidence_min = 0
                confidence_max_column = key_name + '-' + stat_name + '-max'
                confidence_max = 0
                confidence_mean_column = key_name + '-' + stat_name + '-mean'
                confidence_mean = 0
                confidence_median_column = key_name + '-' + stat_name + '-median'
                confidence_median = 0
                if 0 < len(list_value): 
                    confidence_min = min(list_value)
                    confidence_max = max(list_value)
                    confidence_mean = statistics.mean(list_value)
                    confidence_median = statistics.median(list_value)
                collected_stats[confidence_min_column] = confidence_min
                collected_stats[confidence_max_column] = confidence_max
                collected_stats[confidence_mean_column] = confidence_mean
                collected_stats[confidence_median_column] = confidence_median

    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return collected_stats