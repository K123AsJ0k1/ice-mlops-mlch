def qdrant_create_collection(
    qdrant_client: any, 
    collection_name: str,
    configuration: any
) -> any:
    try:
        result = None
        if 'vectors-config' in configuration and not 'sparse-vectors-config' in configuration:
            print('dense')
            result = qdrant_client.create_collection(
                collection_name = collection_name,
                vectors_config = configuration['vectors-config']
            )
        if 'sparse-vectors-config' in configuration and not 'vectors-config' in configuration:
            print('sparse')
            result = qdrant_client.create_collection(
                collection_name = collection_name,
                sparse_vectors_config = configuration['sparse-vectors-config']
            )
        if 'vectors-config' in configuration and 'sparse-vectors-config' in configuration:
            print('hybrid')
            result = qdrant_client.create_collection(
                collection_name = collection_name,
                vectors_config = configuration['vectors-config'],
                sparse_vectors_config = configuration['sparse-vectors-config']
            )
        return result
    except Exception as e:
        print(e)
        return None

def qdrant_get_collection(
    qdrant_client: any, 
    collection_name: str
) -> any:
    try:
        collection = qdrant_client.get_collection(
            collection_name = collection_name
        )
        return collection
    except Exception as e:
        return None

def qdrant_collection_number( 
    qdrant_client: any, 
    collection_name: str,
    count_filter: any
) -> any:
    try:
        result = qdrant_client.count(
            collection_name = collection_name,
            count_filter = count_filter,
            exact =  True
        )
        return result.count
    except Exception as e:
        print(e)
        return None

def qdrant_list_collections(
    qdrant_client: any
) -> any:
    try:
        collections = qdrant_client.get_collections()
        collection_list = []
        for description in collections.collections:
            collection_list.append(description.name)
        return collection_list
    except Exception as e:
        return []
    
def qdrant_remove_collection(
    qdrant_client: any, 
    collection_name: str
) -> bool:
    try:
        qdrant_client.delete_collection(collection_name)
        return True
    except Exception as e:
        return False

def qdrant_upsert_points(
    qdrant_client: any, 
    collection_name: str,
    points: any
) -> any:
    try:
        results = qdrant_client.upsert(
            collection_name = collection_name, 
            points = points
        )
        return results
    except Exception as e:
        print(e)
        return None

def qdrant_search_data(
    qdrant_client: any,  
    collection_name: str,
    scroll_filter: any,
    limit: int,
    offset: any
) -> any:
    try:
        hits = qdrant_client.scroll(
            collection_name = collection_name,
            scroll_filter = scroll_filter,
            limit = limit,
            with_payload = True,
            offset = offset
        )
        return hits
    except Exception as e:
        print(e)
        return []

def qdrant_search_vectors(
    qdrant_client: any,   
    collection_name: str,
    query_vector: any,
    limit: str
) -> any:
    try:
        hits = qdrant_client.search(
            collection_name = collection_name,
            query_vector = query_vector,
            limit = limit
        )
        return hits
    except Exception as e:
        return []

def qdrant_remove_points(
    qdrant_client: any, 
    collection_name: str, 
    points_selector: any
) -> bool:
    try:
        results = qdrant_client.delete(
            collection_name = collection_name,
            points_selector = points_selector
        )
        return results
    except Exception as e:
        print(f"Error removing document: {e}")
        return None
    
def qdrant_create_configuration(
    embedding_size: int
) -> any:
    try:
        from qdrant_client.models import VectorParams, Distance
    except ImportError as e:
        raise ImportError("qdrant/use failed to import", e)

    try:
        collection_configuration = VectorParams(
            size = embedding_size, 
            distance = Distance.COSINE
        )
        return collection_configuration
    except Exception as e:
        print(f"Error creating configuration: {e}")
        return None

def qdrant_create_point(
    point_uuid: str,
    point_dense_vector: any,
    point_sparse_vector: any,
    point_payload: any
) -> any:
    try:
        from qdrant_client.models import PointStruct
    except ImportError as e:
        raise ImportError("qdrant/use failed to import", e)

    try:
        point = None
        if not point_dense_vector is None and point_sparse_vector is None: 
            #print('dense')
            point = PointStruct(
                id = point_uuid, 
                vector = point_dense_vector,
                payload = point_payload
            )
        if not point_sparse_vector is None and point_dense_vector is None:
            #print('sparse')
            point = PointStruct(
                id = point_uuid, 
                vector = point_sparse_vector,
                payload = point_payload
            )
        if not point_dense_vector is None and not point_sparse_vector is None:
            #print('hybrid')
            combined_vectors = {
                **point_dense_vector, 
                **point_sparse_vector
            }
            point = PointStruct(
                id = point_uuid, 
                vector = combined_vectors,
                payload = point_payload
            )
        return point
    except Exception as e:
        print(f"Error creating point: {e}")
        return None
    
def qdrant_upload_points(
    qdrant_client: any, 
    collection_name: str,
    points: list
) -> bool:
    try:
        result = qdrant_client.upload_points(
            collection_name = collection_name, 
            points = points
        )
        return result
    except Exception as e:
        print(f"Error uploading points: {e}")
        return None
    
def qdrant_modifiable_query(
    qdrant_client: any, 
    query_type: str,
    collection_name: str,
    query_dense: any,
    query_sparse: any,
    query_limit: int,
    fusion_limit: int
) -> list:
    try:
        from qdrant_client.models import models
    except ImportError as e:
        raise ImportError("qdrant/use failed to import", e)

    try:
        if query_type == 'dense':
            query_result = qdrant_client.query_points(
                collection_name = collection_name,
                query = query_dense,
                using = "dense",
                limit = query_limit
            )

        if query_type == 'sparse':
            query_result = qdrant_client.query_points(
                collection_name = collection_name,
                query = query_sparse,
                using = "sparse",
                limit = query_limit
            )
        
        if query_type == 'hybrid-rrf':
            query_result = qdrant_client.query_points(
                collection_name = collection_name,
                prefetch = [
                    models.Prefetch(
                        query = query_dense,
                        using = "dense",
                        limit = fusion_limit
                    ),
                    models.Prefetch(
                        query = query_sparse,
                        using = "sparse",
                        limit = fusion_limit
                    )
                ],
                query = models.FusionQuery(fusion=models.Fusion.RRF),
                limit = query_limit
            )
        if query_type == 'hybrid-dbsf':
            query_result = qdrant_client.query_points(
                collection_name = collection_name,
                prefetch = [
                    models.Prefetch(
                        query = query_dense,
                        using = "dense",
                        limit = fusion_limit
                    ),
                    models.Prefetch(
                        query = query_sparse,
                        using = "sparse",
                        limit = fusion_limit
                    )
                ],
                query = models.FusionQuery(fusion=models.Fusion.DBSF),
                limit = query_limit
            )

        return query_result.points
    except Exception as e:
        print(f"Error HSRRF query: {e}")
        return None
    
