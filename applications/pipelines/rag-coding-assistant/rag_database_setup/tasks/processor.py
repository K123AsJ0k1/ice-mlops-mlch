import ray
import time as t
from icebreaker.swift.setup import swift_setup_client
from icebreaker.storage.management import object_storage_interaction
from icebreaker.pyarrow.use import pyarrow_deserialize_dataframe

@ray.remote(
    num_cpus = 1,
    memory = 0.2 * 1024 * 1024 * 1024
) 
def database_setup(
    worker_index: int,
    actor_index: int,
    actor_ref: any,
    swift_parameters: any,
    data_storage_parameters: any,
    config_parameters: any,
    task_batch: any,
    target_profile: dict
) -> any:
    start_time = t.time()
    print(f'Task {worker_index}, Actor {actor_index}')
    
    print('Setting up swift client')
    work_swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )
    print('Swift client setup') 

    analysis_parameters = config_parameters['analysis-parameters']
    filter_parameters = config_parameters['filter-parameters']
    
    language_column = analysis_parameters['language-column']    
    format_column = analysis_parameters['format-column']
    
    allowed_languages = filter_parameters['allowed-languages']
    allowed_formats = filter_parameters['allowed-formats']

    suitable_dataframe_rows = []
    for batch_data in task_batch:
        object_path = batch_data[0]

        max_target_for_this_path = target_profile.get(object_path, 0)

        if max_target_for_this_path <= 0:
            continue
        
        stored_dataset = object_storage_interaction(
            storage_client = work_swift_client,
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
        
        chunk_size = 1000
        total_rows = len(pandas_df)
        path_collected_rows = []
        
        for i in range(0, total_rows, chunk_size):
            if len(path_collected_rows) >= max_target_for_this_path:
                break
                
            df_chunk = pandas_df.iloc[i : i + chunk_size]
            lang_chunk = df_chunk[language_column].tolist()
            format_chunk = df_chunk[format_column].tolist()
            
            text_input_ref_1 = ray.put(lang_chunk)
            lang_future = actor_ref.batch_fasttext_languages.remote(
                worker_index = worker_index, 
                actor_index = actor_index, 
                batch_index = i,
                used_key = object_path, 
                text_input = text_input_ref_1, 
                analysis_parameters = analysis_parameters
            )
            
            text_input_ref_2 = ray.put(format_chunk)
            format_future = actor_ref.batch_magika_formats.remote(
                worker_index = worker_index, 
                actor_index = actor_index, 
                batch_index = i,
                used_key = object_path, 
                text_input = text_input_ref_2, 
                analysis_parameters = analysis_parameters
            )
            
            provider_actor_refs = [lang_future, format_future]
            results = {}
            while len(provider_actor_refs):
                done_refs, provider_actor_refs = ray.wait(provider_actor_refs)
                for ref in done_refs:
                    res = ray.get(ref)
                    if isinstance(res, dict):
                        if 'languages' in res:
                            results['languages'] = res['languages']
                        if 'formats' in res:
                            results['formats'] = res['formats']
                    
            languages = results.get('languages', [])
            formats = results.get('formats', [])
            
            for idx, row_tuple in enumerate(df_chunk.itertuples(index=False)):
                if len(path_collected_rows) >= max_target_for_this_path:
                    break
                
                is_english = (idx < len(languages) and languages[idx] in allowed_languages)
                is_valid_format = (idx < len(formats) and formats[idx] in allowed_formats)
                
                if is_english and is_valid_format:
                    path_collected_rows.append(row_tuple._asdict())
                    
        suitable_dataframe_rows.extend(path_collected_rows)

    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return suitable_dataframe_rows