def mongo_is_client(
    storage_client: any
) -> any:
    try:
        from pymongo import MongoClient as mc
    except ImportError as e:
        raise ImportError("mongo/setup failed to import", e)

    return isinstance(storage_client, mc.Connection)

def mongo_setup_client(
    username: str,
    password: str,
    address: str,
    port: str
) -> any:
    try:
        from pymongo import MongoClient as mc
    except ImportError as e:
        raise ImportError("mongo/setup failed to import", e)

    connection_prefix = 'mongodb://(username):(password)@(address):(port)/'
    connection_address = connection_prefix.replace('(username)', username)
    connection_address = connection_address.replace('(password)', password)
    connection_address = connection_address.replace('(address)', address)
    connection_address = connection_address.replace('(port)', port)
    mongo_client = mc(
        host = connection_address
    )
    return mongo_client