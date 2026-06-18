import ray
import statistics
import time as t
from icebreaker.swift.setup import swift_setup_client
from icebreaker.storage.management import object_storage_interaction
from icebreaker.pd_stats.use import (
    stats_pandas_content
)
from icebreaker.pyarrow.use import pyarrow_deserialize_dataframe

@ray.remote(
    num_cpus = 1,
    memory = 0.2 * 1024 * 1024 * 1024
) 
def data_processor(
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
     
    provider_actor_refs = []
    batch_index = 1
    for batch_data in task_batch:
        object_path = batch_data[0]
        
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
        # Most likely there is a need for dataset limit 
        chunk_size = 1000
        total_rows = len(pandas_df)
        for i in range(0, total_rows, chunk_size):
            lang_chunk = pandas_df[language_column].iloc[i : i + chunk_size].tolist()
            format_chunk = pandas_df[format_column].iloc[i : i + chunk_size].tolist()
            
            text_input_ref_1 = ray.put(lang_chunk)
            provider_actor_refs.append(actor_ref.batch_fasttext_languages.remote(
                worker_index = worker_index,
                actor_index = actor_index,
                batch_index = batch_index,
                used_key = object_path,
                text_input = text_input_ref_1,
                analysis_parameters = analysis_parameters
            ))
            
            text_input_ref_2 = ray.put(format_chunk)
            provider_actor_refs.append(actor_ref.batch_magika_formats.remote(
                worker_index = worker_index,
                actor_index = actor_index,
                batch_index = batch_index,
                used_key = object_path,
                text_input = text_input_ref_2,
                analysis_parameters = analysis_parameters
            ))
            
        batch_index += 1
    
    while len(provider_actor_refs):
        done_actor_refs, provider_actor_refs = ray.wait(provider_actor_refs)
        for output_ref in done_actor_refs: 
            result = ray.get(output_ref)
            # Here we filter for english and want python, bash, yaml or markdown

    suitable_dataframe_rows = []

    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return suitable_dataframe_rows