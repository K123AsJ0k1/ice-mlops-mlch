
#import ray

#import re
#import hashlib

#from qdrant_client.models import VectorParams, Distance, PointStruct

#from langchain_text_splitters import Language

#from functions.utility import generate_uuid, batch_list
#from functions.documents import get_sorted_documents
#from functions.mongo_db import mongo_setup_client
#from functions.langchain import langchain_create_code_chunks, langchain_create_text_chunks
#from functions.qdrant_vb import qdrant_setup_client, qdrant_list_collections, qdrant_create_collection, qdrant_upsert_points

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
