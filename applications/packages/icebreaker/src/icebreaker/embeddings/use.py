
def embeddings_create_hybrid_points(
    dataset_name: str,
    target_df: any,
    text_column: str,
    text_encoder: any,
    global_vocabulary: dict
) -> list:
    try:
        from qdrant_client import models
        from ..sparse.use import sparse_create_tuple
        from ..qdrant.use import qdrant_create_point
        from ..embeddings.utility import embeddings_generate_uuid
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)
    points = []
    for i, row in enumerate(target_df.to_dict('records')):
        text_data = row[text_column]

        dense_vector = text_encoder.encode(text_data).tolist()
        indices, values = sparse_create_tuple(
            global_vocabulary,
            vector_text = text_data
        )
        sparse_vector = models.SparseVector(indices=indices, values=values)
        
        point_uuid = embeddings_generate_uuid(
            id = dataset_name,
            index = i
        )

        created_point = qdrant_create_point(
            point_uuid = point_uuid,
            point_dense_vector = {"dense": dense_vector},
            point_sparse_vector = {"sparse": sparse_vector},
            point_payload = row
        )

        points.append(created_point)
    return points, global_vocabulary
    
def embeddings_check_collection(
    vector_client: any,
    vector_collection: str,
    embedding_size: int
) -> bool:
    try:
        from ..qdrant.use import (
            qdrant_list_collections,
            qdrant_create_configuration,
            qdrant_create_collection
        )
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)

    vector_collections = qdrant_list_collections(
        qdrant_client = vector_client
    )
    
    collection_created = False
    if not vector_collection in vector_collections:
        try:
            collection_configuration = qdrant_create_configuration(
                embedding_size = embedding_size
            )
            collection_created = qdrant_create_collection(
                qdrant_client = vector_client,
                collection_name = vector_collection,
                configuration = collection_configuration
            )
        except Exception as e:
            print(e)
    return collection_created

def embeddings_create_point(
    id: any,
    index: any,
    embedding_vector: any,
    embedding_payload: any
):
    try:
        from ..qdrant.use import (
            qdrant_create_point
        )
        from ..embeddings.utility import embeddings_generate_uuid
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)

    embedding_uuid = embeddings_generate_uuid(
        id = id,
        index = index
    )

    embedding_point = qdrant_create_point(
        embedding_uuid = embedding_uuid,
        embedding_vector = embedding_vector,
        embedding_payload = embedding_payload
    )
    return embedding_point

def embeddings_get_checked(
    object_client: any,
    storage_parameters: any,
    prefix: str
):
    try:
        from ..minio.use import (
            minio_check_object,
            minio_get_object_data_and_metadata
        )
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)

    used_object_bucket = storage_parameters['object-bucket']
    used_object_path = storage_parameters['object-path'] + '-' + prefix
    
    object_exists = minio_check_object(
        minio_client = object_client,
        bucket_name = used_object_bucket, 
        object_path = used_object_path
    )

    data = []
    if object_exists:
        data = minio_get_object_data_and_metadata(
            minio_client = object_client,
            bucket_name = used_object_bucket, 
            object_path = used_object_path
        )['data']
    return data

def embeddings_store_checked(
    object_client: any,
    storage_parameters: any,
    prefix: str,
    checked: any
):
    try:
        from ..minio.use import (
            minio_create_or_update_object
        )
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)

    used_object_bucket = storage_parameters['object-bucket']
    used_object_path = storage_parameters['object-path'] + '-' + prefix
    
    minio_create_or_update_object(
        minio_client = object_client,
        bucket_name = used_object_bucket, 
        object_path = used_object_path,
        data = checked, 
        metadata = {}
    )

def embeddings_remove_duplicate_vectors(
    vector_client: any
):
    try:
        from ..qdrant.use import (
            qdrant_list_collections,
            qdrant_collection_number,
            qdrant_search_data,
            qdrant_remove_points
        )
        from qdrant_client.models import PointIdsList
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)

    collections = qdrant_list_collections(
        qdrant_client = vector_client
    )
    # This might be parallizable
    for collection in collections:
        print('Cleaning collection ' + str(collection))
        collection_number = qdrant_collection_number(
            qdrant_client = vector_client, 
            collection_name = collection,
            count_filter = {}
        )

        print('Collection vectors: ' + str(collection_number))

        batch_size = 200
        scroll_offset = None

        unique_point_ids = set()
        unique_chunk_hashes = set()
        duplicate_vectors = []
        while True:
            vectors = qdrant_search_data(
                qdrant_client = vector_client,  
                collection_name = collection,
                scroll_filter = {},
                limit = batch_size,
                offset = scroll_offset
            )
            
            for vector in vectors[0]:
                chunk_hash = vector.payload['chunk_hash']
                vector_id = vector.id
                # Scroll can cause double count
                # so id check is needed
                if not vector_id in unique_point_ids:
                    unique_point_ids.add(vector_id)
                    if not chunk_hash in unique_chunk_hashes:
                        unique_chunk_hashes.add(chunk_hash)
                    else:
                        duplicate_vectors.append(vector_id)

            if len(vectors[0]) < batch_size:
                break

            scroll_offset = vectors[0][-1].id

        print('Found unique vectors: ' + str(len(unique_chunk_hashes)))
        print('Found duplicate vectors: ' + str(len(duplicate_vectors)))
        if 0 < len(duplicate_vectors):
            status = qdrant_remove_points(
                qdrant_client = vector_client,  
                collection_name = collection, 
                points_selector = PointIdsList(
                    points = duplicate_vectors
                )
            ) 
