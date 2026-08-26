import ray
import time as t
from icebreaker.swift.setup import swift_setup_client
from icebreaker.storage.management import object_storage_interaction
from icebreaker.pyarrow.use import pyarrow_deserialize_dataframe

@ray.remote(
    num_cpus = 1,
    memory = 0.2 * 1024 * 1024 * 1024
) 
def data_filter(
    worker_index: int,
    actor_index: int,
    actor_ref: any,
    swift_parameters: any,
    data_storage_parameters: any,
    config_parameters: any,
    task_batch: any,
    worker_targets: dict
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
        dataset_name = object_path.split('/')[-1].split('.')[0]
        wanted_rows = worker_targets.get(object_path, 0)
        if wanted_rows <= 0:
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
        
        total_rows = len(pandas_df)
        calclated_chunk = int(total_rows * 0.05)
        chunk_size = max(1, calclated_chunk)
        path_collected_rows = []
        row_idx = 0
        for i in range(0, total_rows, chunk_size):
            if wanted_rows <= len(path_collected_rows):
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
            chunk_languages = []
            chunk_formats = []
            while len(provider_actor_refs):
                done_actor_refs, provider_actor_refs = ray.wait(provider_actor_refs)
                for output_ref in done_actor_refs: 
                    res = ray.get(output_ref)
                    if 'languages' in res:
                        chunk_languages = res['languages']
                    if 'formats' in res:
                        chunk_formats = res['formats']
            
            for idx, row in enumerate(df_chunk.itertuples(index=False)):
                if wanted_rows <= len(path_collected_rows):
                    break

                row_language_tuple = chunk_languages[idx]
                row_language = str(row_language_tuple[0])
                row_format_tuple = chunk_formats[idx]
                row_format = str(row_format_tuple[0])
                # This is tuple ('en', 0.8225014209747314) and (markdown, 0.721967339515686)
                if row_language in allowed_languages:
                    if row_format in allowed_formats:
                        wanted_row = [
                            row[0],
                            row[1],
                            row_language,
                            row_format,
                            dataset_name,
                            row_idx
                        ]
                        path_collected_rows.append(wanted_row)
                row_idx += 1
        suitable_dataframe_rows.extend(path_collected_rows)
    
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return suitable_dataframe_rows