def pyarrow_serialize_dataframe(
    dataframe: any
) -> any:
    try:
        from io import BytesIO
    except ImportError as e:
        raise ImportError("Failed to import", e)

    buffer = BytesIO()
    dataframe.to_parquet(buffer, index = False)
    buffer.seek(0)
    serialized_data = buffer.getvalue()
    return serialized_data

def pyarrow_deserialize_dataframe(
    serialized_dataframe: any
) -> any:
    try:
        from io import BytesIO
        import pandas as pd
    except ImportError as e:
        raise ImportError("Failed to import", e)

    deserialized_data = BytesIO(serialized_dataframe)
    restored_dataframe = pd.read_parquet(deserialized_data)
    return restored_dataframe