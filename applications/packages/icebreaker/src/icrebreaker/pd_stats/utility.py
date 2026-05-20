def pandas_modify_dataframe(
    column_types: any,
    df: any
) -> any:
    for name in df.columns:
        wanted_type = column_types[name]
        if df[name].isna().any():
            if wanted_type == 'object':
                df[name] = df[name].fillna('null')
            if wanted_type == 'int64' or wanted_type == 'float64':
                df[name] = df[name].fillna(0)
    df = df.astype(column_types)
    return df