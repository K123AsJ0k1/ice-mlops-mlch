
def embeddings_batch_create_vectors(
    text_input_batch: list,
    dense_model: any,
    sparse_model: any,
):
    try: 
        from qdrant_client import models
        from ..dense.use import dense_create_baai_vectors
        from ..sparse.use import sparse_create_spalde_embeddings
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)
    
    dense_vectors = []
    if not dense_model is None:
        dense_vectors = dense_create_baai_vectors(
            dense_model = dense_model,
            text_inputs = text_input_batch
        )
    sparse_vectors = []
    if not sparse_model is None:
        sparse_embeddings_iter = sparse_create_spalde_embeddings(
            sparse_model = sparse_model,
            text_inputs = text_input_batch
        )
        
        sparse_vectors = [
            models.SparseVector(
                indices=emb.indices.tolist(),
                values=emb.values.tolist()
            )
            for emb in sparse_embeddings_iter
        ]

    return dense_vectors, sparse_vectors

def embeddings_create_hybrid_points(
    dataset_name: str,
    dataset_records: dict,
    text_column: str,
    dense_model: any,
    sparse_model: any,
) -> list:
    try: 
        from ..qdrant.use import qdrant_create_point
        from ..embeddings.utility import embeddings_generate_uuid
    except ImportError as e:
        raise ImportError("embeddings/use failed to import", e)
    
    text_data_list = [row[text_column] for row in dataset_records]

    dense_vectors, sparse_vectors = embeddings_batch_create_vectors(
        text_input_batch = text_data_list,
        dense_model = dense_model,
        sparse_model = sparse_model
    ) 

    points = []
    for i, row in enumerate(dataset_records):
        d_vec = dense_vectors[i] if dense_vectors is not None else None
        s_vec = sparse_vectors[i] if sparse_vectors is not None else None

        point_uuid = embeddings_generate_uuid(
            id = dataset_name,
            index = i
        )

        created_point = qdrant_create_point(
            point_uuid = point_uuid,
            point_dense_vector = {"dense": d_vec} if d_vec else None,
            point_sparse_vector = {"sparse": s_vec} if s_vec else None,
            point_payload = row
        )
        points.append(created_point)

    return points
    
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
