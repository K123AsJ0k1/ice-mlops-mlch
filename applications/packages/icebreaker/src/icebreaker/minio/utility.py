def minio_pickle_data(
    data: any
) -> any:
    try:
        import io
        import pickle
    except ImportError as e:
        raise ImportError("minio/utility failed to import", e)

    pickled_data = pickle.dumps(data)
    length = len(pickled_data)
    buffer = io.BytesIO()
    buffer.write(pickled_data)
    buffer.seek(0)
    return buffer, length

def minio_unpickle_data(
    pickled: any
) -> any:
    try:
        import pickle
    except ImportError as e:
        raise ImportError("minio/utility failed to import", e)

    return pickle.loads(pickled)