from io import BytesIO

def pyarrow_serialize_dataframe(
    dataframe: any
) -> any:
    buffer = BytesIO()
    dataframe.to_parquet(buffer, index = True)
    buffer.seek(0)
    serialized_data = buffer.getvalue()
    return serialized_data