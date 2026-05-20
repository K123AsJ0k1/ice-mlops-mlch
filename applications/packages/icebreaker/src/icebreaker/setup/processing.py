
def processing_save_data(
    dataset_repository: str,
    dataset_name: str,
    hf_token: str,
    table_size: int,
    size_limit: int,
    relevant_columns: list,
    renamed_columns: dict,
    target_directory: str
) -> int:
    try:
        import time as t
        from pathlib import Path
        import pandas as pd
        import dask.dataframe as dd
        from datasets import load_dataset
    except ImportError as e:
        raise ImportError("Failed to import", e)

    start_time = t.time()
    data_stream = load_dataset(
        dataset_repository, 
        dataset_name,
        split = 'train',
        streaming = True,
        token = hf_token
    )

    dask_dfs = []
    batch = []
    row_index = 0
    batch_index = 0
    for i, row in enumerate(data_stream):
        if size_limit <= (i + 1):
            break
        batch.append(row)
        row_index += 1
        if (row_index) % table_size == 0:
            batch_df = pd.DataFrame(batch) 
            dask_df = dd.from_pandas(batch_df, npartitions = 1)
            dask_dfs.append(dask_df)
            batch = []
            batch_index += 1
    if batch:
        batch_df = pd.DataFrame(batch) 
        dask_df = dd.from_pandas(batch_df, npartitions = 1)
        dask_dfs.append(dask_df)
        batch = []
        batch_index += 1
    processing_dask_df = dd.concat(dask_dfs)

    processing_dask_df = processing_dask_df[relevant_columns].rename(columns = renamed_columns)

    partitions = processing_dask_df.to_delayed()
    table_index = 1
    for i, partition in enumerate(partitions):
        data_name = dataset_repository.split('/')[-1] + '-' + dataset_name
        file_path = target_directory + '/' + data_name + '-' + str(table_index) + '.parquet'
        output_path = Path(file_path)
        print('Storing partition into:', output_path)
        computed_partition = partition.compute()
        computed_partition.to_parquet(output_path, engine = 'pyarrow')
        table_index += 1 
        
    end_time = t.time()
    total_time = round(end_time-start_time,5)
    print('Spent seconds', total_time)
    return total_time