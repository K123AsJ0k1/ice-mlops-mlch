import ray
import time as t

from icebreaker.swift.setup import swift_setup_client
from icebreaker.objects.use import objects_get_data
from icebreaker.rag.utility import rag_format_data
from icebreaker.objects.use import objects_store_data, objects_get_prefix_list
from icebreaker.storage.management import storage_set_object_path

@ray.remote(
    num_cpus = 1,
    memory = 0.2 * 1024 * 1024 * 1024
) 
def database_evalution(
    worker_index: int,
    actor_index: int,
    actor_ref: any,
    swift_parameters: dict,
    collection_name: str,
    input_storage_parameters: dict,
    output_storage_parameters: dict,
    config_parameters: dict,
    task_batch: list 
) -> dict: 
    start_time = t.time()
    print(f'Task {worker_index}, Actor {actor_index}')
    
    swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )
    print('Swift client setup') 

    process_batch_size = config_parameters['batch-size']
    generator_actor_refs = []
    stored_dfs = {}
    for data_index, batch_data in enumerate(task_batch):
        object_path = batch_data[0]
        
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
        
        pandas_df = data_object[0]
        key_name = object_path.split('/')[-1].split('.')[0]
        stored_dfs[key_name] = pandas_df
 
    query_column = config_parameters['query-column']
    weight_column = config_parameters['weight-column']
    query_type = config_parameters['query-type']
    relevance_threshold = config_parameters['relevance-threshold']
    query_limit = config_parameters['query-limit']
    fusion_limit = config_parameters['fusion-limit']
    generator_actor_refs = []
    for dataset_name, df in stored_dfs.items():
        df_text_queries = df[query_column].tolist()
        df_relevant_weights = df[weight_column].tolist()

        text_query_ref = ray.put(df_text_queries)
        relevant_weight_ref = ray.put(df_relevant_weights)
        generator_actor_refs.append(actor_ref.batch_generate_queries.remote(
            key_name = dataset_name,
            query_type = query_type,
            collection_name = collection_name,
            text_query_batch = text_query_ref,
            relevant_weights_batch = relevant_weight_ref,
            relevance_threshold = relevance_threshold,
            query_limit = query_limit,
            fusion_limit = fusion_limit,
            batch_size = process_batch_size
        ))

    retrieval_outputs = {
        'parameters': {
            'type': query_type,
            'query-limit': query_limit,
            'fusion-limit': fusion_limit,
            'relevance-threshold': relevance_threshold,
            'batch-size': process_batch_size
        },
        'tables': {}
    }

    while len(generator_actor_refs) > 0:
        done_refs, generator_actor_refs = ray.wait(generator_actor_refs)
        for output_ref in done_refs: 
            batch = ray.get(output_ref)
            key_name = batch['key_name']
            retrieval_outputs['tables'][key_name] = batch
            
    formatted_rag_data = rag_format_data(
        retrieval_outputs = retrieval_outputs,
        metric_columns = [
            'p@1',
            'r@3',
            'rr',
            'ap',
            'ndcg@3',
            'ndcg@5',
            'embedding-latency-ms',
            'search-latency-ms',
            'total-latency-ms',
            'total-characters'
        ]
    )

    name_start_prefix = output_storage_parameters['name-start-prefix']
    output_storage_parameters['debug-prints'] = True
    output_storage_parameters['lock-parameters'] = {}
    output_storage_parameters['lock-location'] = None
    output_storage_parameters['overwrite'] = True

    parameters = formatted_rag_data['parameters']
    for dataset_name in formatted_rag_data['metrics'].keys():
        metrics = formatted_rag_data['metrics'][dataset_name]
        table = formatted_rag_data['tables'][dataset_name]
        used_identity = dataset_name.split('extraction-data')[1][1:]

        artifact = {
            'parameters': parameters,
            'metrics': metrics
        }

        artifact_object_name = 'arti'
        artifact_path_replacers = {
            'name': 'METRICS'
        }
    
        artifact_path_name = f'{name_start_prefix}-rag-metrics-{used_identity}-'

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
        
        table_path_name = f'{name_start_prefix}-rag-data-{used_identity}.parquet'
        
        output_storage_parameters['object-name'] = 'data'
        output_storage_parameters['object-serialization'] = 'parquet'
        output_storage_parameters['path-replacers'] = {
            'name': 'EVALUATION'
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
    return formatted_rag_data