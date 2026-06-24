
def mongo_get_database(
    mongo_client: any,
    database_name: str
) -> any:
    try:
        database = mongo_client[database_name]
        return database
    except Exception as e:
        return None

def mongo_check_database(
    mongo_client: any, 
    database_name: str
) -> bool:
    try:
        database_exists = database_name in mongo_client.list_database_names()
        return database_exists
    except Exception as e:
        return False

def mongo_list_databases(
    mongo_client: any
) -> any:
    try:
        databases = mongo_client.list_database_names()
        return databases
    except Exception as e:
        return []

def mongo_remove_database(
    mongo_client: any, 
    database_name: str
) -> bool:
    try:
        mongo_client.drop_database(database_name)
        return True
    except Exception as e:
        return False

def mongo_get_collection(
    mongo_client: any, 
    database_name: str, 
    collection_name: str
) -> bool:
    try:
        database = mongo_get_database(
            mongo_client = mongo_client,
            database_name = database_name
        )
        collection = database[collection_name]
        return collection
    except Exception as e:
        return None
    
def mongo_check_collection(
    mongo_client: any, 
    database_name: any, 
    collection_name: any
) -> bool:
    try:
        database = mongo_client[database_name]
        collection_exists = collection_name in database.list_collection_names()
        return collection_exists
    except Exception as e:
        return False

def mongo_update_collection(
    mongo_client: any, 
    database_name: str, 
    collection_name: str, 
    filter_query: any, 
    update_query: any
) -> any:
    try:
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        result = collection.update_many(filter_query, update_query)
        return result
    except Exception as e:
        return None

def mongo_list_collections(
    mongo_client: any, 
    database_name: str
) -> bool:
    try:
        database = mongo_get_database(
            mongo_client = mongo_client,
            database_name = database_name
        )
        collections = database.list_collection_names()
        return collections
    except Exception as e:
        return []

def mongo_remove_collection(
    mongo_client: any, 
    database_name: str, 
    collection_name: str
) -> bool:
    try: 
        database = mongo_get_database(
            mongo_client = mongo_client,
            database_name = database_name
        )
        database.drop_collection(collection_name)
        return True
    except Exception as e:
        return False

def mongo_create_document(
    mongo_client: any, 
    database_name: str, 
    collection_name: str, 
    document: any
) -> any:
    try: 
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        result = collection.insert_one(document)
        return result
    except Exception as e:
        return None

def mongo_get_document(
    mongo_client: any, 
    database_name: str, 
    collection_name: str, 
    filter_query: any
):
    try: 
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        document = collection.find_one(filter_query)
        return document
    except Exception as e:
        print(e)
        return None 
    
def mongo_collection_number(
    mongo_client: any, 
    database_name: str, 
    collection_name: str 
) -> any:
    try:
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        amount_of_documents = collection.count_documents({})
        return amount_of_documents
    except Exception as e:
        return None

def mongo_list_documents(
    mongo_client: any, 
    database_name: str, 
    collection_name: str, 
    filter_query: any,
    sorting_query: any
) -> any:
    try: 
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        documents = list(collection.find(filter_query).sort(sorting_query))
        return documents
    except Exception as e:
        return []

def mongo_update_document(
    mongo_client: any, 
    database_name: any, 
    collection_name: any, 
    filter_query: any, 
    update_query: any
) -> any:
    try: 
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        result = collection.update_one(filter_query, update_query)
        return result
    except Exception as e:
        return None

def mongo_remove_document(
    mongo_client: any, 
    database_name: str, 
    collection_name: str, 
    filter_query: any
) -> bool:
    try: 
        collection = mongo_get_collection(
            mongo_client = mongo_client, 
            database_name = database_name, 
            collection_name = collection_name
        )
        result = collection.delete_one(filter_query)
        return result
    except Exception as e:
        return None
    
def mongo_get_sorted_documents(
    document_client: any,
    database: str,
    collection: str
) -> any:
    try: 
        from pymongo import ASCENDING
    except ImportError as e:
        raise ImportError("mongo/use failed to import", e)
    # Edit later
    collection_documents = mongo_list_documents(
        mongo_client = document_client,
        database_name = database,
        collection_name = collection,
        filter_query = {},
        sorting_query = [
            ('index', ASCENDING),
            ('sub-index', ASCENDING)
        ]
    )
    return collection_documents
