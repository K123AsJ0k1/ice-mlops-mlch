import ray
import time as t

from icebreaker.swift.setup import swift_setup_client
from icebreaker.objects.use import objects_get_data
from icebreaker.qdrant.use import qdrant_create_point
from icebreaker.embeddings.utility import embeddings_generate_uuid

@ray.remote(
    num_cpus = 1,
    memory = 0.2 * 1024 * 1024 * 1024
) 
def database_points(
    worker_index: int,
    actor_index: int,
    actor_ref: any,
    swift_parameters: any,
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

    text_column = config_parameters['text-column']
    generator_actor_refs = []
    data_index = 0
    dataset_records = []
    for batch_data in task_batch:
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
        dataset_records.append(df_records)

        total_rows = len(pandas_df)
        calclated_chunk = int(total_rows * 0.05)
        chunk_size = max(1, calclated_chunk)
        for i in range(0, total_rows, chunk_size):
            df_chunk = pandas_df.iloc[i : i + chunk_size]
            text_chunk = df_chunk[text_column].tolist()
            
            text_input_ref_1 = ray.put(text_chunk)
            generator_actor_refs.append(actor_ref.batch_generate_vectors.remote(
                worker_index = worker_index, 
                actor_index = actor_index, 
                data_index = data_index,
                batch_index = i,
                object_path = object_path, 
                text_input = text_input_ref_1
            ))
        data_index += 1

    results = []
    while len(provider_actor_refs):
        done_actor_refs, provider_actor_refs = ray.wait(provider_actor_refs)
        for output_ref in done_actor_refs: 
            res = ray.get(output_ref)
            results.extend(res)
    
    hybrid_points = []
    vector_idx = 0
    for j, batch in enumerate(results):
        batch_dataset_index = batch['data_idx']
        batch_object_path = batch[object_path]
        dense_vectors = batch['dense']
        sparse_vectors = batch['sparse']

        dataset_name = batch_object_path.split('/')[-1].split('.')[0]

        for batch_vector_index in range(0, len(dense_vectors)):
            d_vec = dense_vectors[batch_vector_index] if dense_vectors is not None else None
            s_vec = sparse_vectors[batch_vector_index] if sparse_vectors is not None else None

            dataset_row = dataset_records[batch_dataset_index][vector_idx]

            point_uuid = embeddings_generate_uuid(
                id = dataset_name,
                index = vector_idx
            )

            created_point = qdrant_create_point(
                point_uuid = point_uuid,
                point_dense_vector = {"dense": d_vec} if d_vec else None,
                point_sparse_vector = {"sparse": s_vec} if s_vec else None,
                point_payload = dataset_row
            )
            hybrid_points.append(created_point)

            vector_idx += 1
    
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return hybrid_points