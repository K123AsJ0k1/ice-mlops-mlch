
def get_divided_collections(
    document_client: any,
    data_parameters: any,
    number: int
) -> any:
    try:
        from ..mongo.use import (
            mongo_list_databases,
            mongo_list_collections,
            mongo_collection_number
        )
        from ..pararellism.division import division_data_round_robin
    except ImportError as e:
        raise ImportError("documents/use failed to import", e)

    database_list = mongo_list_databases(
        mongo_client = document_client
    )

    storage_structure = {}    
    # Edit later
    database_prefix = ''
    for database_name in database_list:
        if database_prefix in database_name:
            collection_list = mongo_list_collections(
                mongo_client = document_client,
                database_name = database_name
            )
            storage_structure[database_name] = collection_list
    
    type_priority = data_parameters['document-type-priority']
    collection_tuples = []
    for database_name, collections in storage_structure.items():
        for collection_name in collections:
            collection_type = database_name.split('|')[-1]
            collection_priority = type_priority[collection_type]
            amount_of_documents = mongo_collection_number(
                mongo_client = document_client,
                database_name = database_name,
                collection_name = collection_name
            )
            tuple = (database_name, collection_name, collection_priority, amount_of_documents)
            collection_tuples.append(tuple)
            
    print('Amount of collections: ' + str(len(collection_tuples)))

    return division_data_round_robin(
        target_list = collection_tuples, 
        number = number
    )
