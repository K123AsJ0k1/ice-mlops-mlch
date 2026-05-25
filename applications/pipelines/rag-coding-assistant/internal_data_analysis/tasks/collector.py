import ray
import pickle
import time as t
from icebreaker.swift.setup import swift_setup_client
from icebreaker.storage.management import object_storage_interaction
from icebreaker.pd_stats.use import (
    stats_pandas_max,
    stats_pandas_groupby_max,
    stats_pandas_format,
    stats_pandas_basic,
    stats_pandas_material,
    stats_pandas_paths
)
 
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
    setup_swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )
    print('Swift client setup') 

    analysis_parameters = config_parameters['analysis-parameters']
    
    language_column = analysis_parameters['language-column']
    
    format_column = analysis_parameters['format-column']
    format_replacer = analysis_parameters['format-replacer']
    collected_stats = {}
    provider_actor_refs = []
    batch_index = 1
    for batch_data in task_batch:
        object_path = batch_data[0]
        key_name = object_path.split('/')[-1].split('.')[0]

        if key_name not in collected_stats:
            collected_stats[key_name] = {}

        stored_dataset = object_storage_interaction(
            storage_client = setup_swift_client,
            lock_parameters = {},
            lock_location = None,
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
                'overwrite': True
            },
            object_data = None,
            object_metadata = None
        ) 
        pandas_df = pickle.loads(stored_dataset[0])
        
        # index
        collected_stats[key_name]['index'] = key_name.split('-')[-1]
        # amount
        amount = pandas_df.shape[0]
        collected_stats[key_name]['amount'] = amount
        # chapters
        stats_pandas_max(
            df = pandas_df, 
            column = 'chapter', 
            collection_key = key_name,
            stat_key = 'chapters',
            collected_statistics = collected_stats
        )
        # chapter-index-(key)
        stats_pandas_groupby_max(
            df = pandas_df,
            group_column = 'chapter',
            target_column = 'index',
            collection_key = key_name,
            column_prefix = 'chapter',
            collected_statistics = collected_stats
        )
        # documents
        stats_pandas_max(
            df = pandas_df, 
            column = 'document', 
            collection_key = key_name,
            stat_key = 'documents',
            collected_statistics = collected_stats
        )
        # format-(type)-count
        stats_pandas_format(
            df = pandas_df,
            target_column = format_column,
            format_replacer = format_replacer,
            collection_key = key_name,
            column_prefix = 'format',
            collected_statistics = collected_stats
        )
        # row-(method)
        stats_pandas_basic(
            df = pandas_df,
            column = 'rows',
            collection_key = key_name,
            collected_statistics = collected_stats
        )
        # characters-(method)
        stats_pandas_basic(
            df = pandas_df,
            column = 'characters',
            collection_key = key_name,
            collected_statistics = collected_stats
        )
        # material-(method)
        stats_pandas_material(
            df = pandas_df,
            group_column = 'chapter',
            target_column = 'ref-material',
            collection_key = key_name,
            column_prefix = 'material',
            collected_statistics = collected_stats
        )
        # paths-(method)
        stats_pandas_paths(
            df = pandas_df,
            group_column = 'chapter',
            target_column = 'ref-paths',
            format_replacer = format_replacer,
            collection_key = key_name,
            column_prefix = 'paths',
            collected_statistics = collected_stats
        )
        # Speaking language-(type)
        text_input_ref = ray.put(pandas_df[language_column])
        provider_actor_refs.append(actor_ref.batch_fasttext_stats.remote(
            worker_index = worker_index,
            actor_index = actor_index,
            batch_index = batch_index,
            used_key = key_name,
            text_input = text_input_ref,
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
            # For some reason the metrics order isnt consitent
            for stat_name, value in stats.items():
                collected_stats[key_name][stat_name] = value
    
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return collected_stats