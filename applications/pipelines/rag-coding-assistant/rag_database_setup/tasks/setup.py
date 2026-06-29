import ray
import time as t

from icebreaker.swift.setup import swift_setup_client
from icebreaker.objects.use import objects_get_data
from icebreaker.qdrant.setup import qdrant_setup_client
from icebreaker.qdrant.use import qdrant_create_point, qdrant_upload_points
from icebreaker.embeddings.utility import embeddings_generate_uuid


@ray.remote(
    num_cpus = 1,
    memory = 0.2 * 1024 * 1024 * 1024
) 
def database_setup(
    worker_index: int,
    actor_index: int,
    actor_ref: any,
    swift_parameters: any,
    qdrant_parameters: any,
    collection_name: str,
    data_storage_parameters: any,
    config_parameters: any,
    task_batch: any
) -> any: 
    start_time = t.time()
    print(f'Task {worker_index}, Actor {actor_index}')
    
    work_swift_client = swift_setup_client(
        swift_parameters = swift_parameters
    )
    print('Swift client setup') 

    work_qdrant_client = qdrant_setup_client(
        qdrant_parameters = qdrant_parameters
    )

    text_column = config_parameters['text-column']
    generator_actor_refs = []
    dataset_records_map = {}
    for data_index, batch_data in enumerate(task_batch):
        object_path = batch_data[0]
        
        data_object = objects_get_data(
            swift_client = work_swift_client,
            storage_parameters = {
                'bucket-target': data_storage_parameters['bucket-target'],
                'bucket-prefix': data_storage_parameters['bucket-prefix'],
                'bucket-user': data_storage_parameters['bucket-user'],
                'object-name': 'root',
                'object-serialization': data_storage_parameters['object-serialization'],
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
        df_records = pandas_df.to_dict('records')
        dataset_records_map[data_index] = df_records

        total_rows = len(pandas_df)
        calclated_chunk = int(total_rows * 0.05)
        chunk_size = max(1, calclated_chunk)
        for i in range(0, total_rows, chunk_size):
            df_chunk = pandas_df.iloc[i : i + chunk_size]
            text_chunk = df_chunk[text_column].tolist()
            # Retain absolute index tracking within this individual file
            chunk_row_indices = list(range(i, i + len(df_chunk)))
            
            text_input_ref = ray.put(text_chunk)
            generator_actor_refs.append(actor_ref.batch_generate_vectors.remote(
                worker_index = worker_index, 
                actor_index = actor_index, 
                data_index = data_index,
                batch_index = i,
                object_path = object_path, 
                text_input = text_input_ref,
                row_indices = chunk_row_indices
            ))
    
    results = []
    while len(provider_actor_refs):
        done_actor_refs, provider_actor_refs = ray.wait(provider_actor_refs)
        for output_ref in done_actor_refs: 
            res = ray.get(output_ref)
            results.extend(res)
    
    hybrid_points = []
    while len(generator_actor_refs) > 0:
        done_refs, generator_actor_refs = ray.wait(generator_actor_refs)
        for output_ref in done_refs: 
            batch = ray.get(output_ref)
            
            batch_dataset_index = batch['data_idx']
            batch_object_path = batch['object_path']
            dense_vectors = batch['dense']
            sparse_vectors = batch['sparse']
            row_indices = batch['row_indices']

            dataset_name = batch_object_path.split('/')[-1].split('.')[0]
            source_records = dataset_records_map[batch_dataset_index]

            for idx_in_chunk, actual_row_idx in enumerate(row_indices):
                d_vec = dense_vectors[idx_in_chunk] if dense_vectors is not None else None
                s_vec = sparse_vectors[idx_in_chunk] if sparse_vectors is not None else None
                
                # Fetch exact correct row payload matching this vector
                dataset_row = source_records[actual_row_idx]

                # Fixed index alignment bugs via actual_row_idx
                point_uuid = embeddings_generate_uuid(
                    id = dataset_name,
                    index = actual_row_idx
                )

                created_point = qdrant_create_point(
                    point_uuid = point_uuid,
                    point_dense_vector = {"dense": d_vec} if d_vec else None,
                    point_sparse_vector = {"sparse": s_vec} if s_vec else None,
                    point_payload = dataset_row
                )
                hybrid_points.append(created_point)
    
    status = qdrant_upload_points(
        qdrant_client = work_qdrant_client, 
        collection_name = collection_name,
        points = hybrid_points
    ) 

    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return True