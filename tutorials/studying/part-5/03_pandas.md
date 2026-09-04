---
technologies: "Pandas"
category: "Choice and use of technology"
difficulty: "Easy"
---

# Pandas

## Used material

1. <span id="used-material-1"></span> [Pandas pip package](https://pypi.org/project/pandas/)

2. <span id="used-material-2"></span> [Pandas docs](https://pandas.pydata.org/)

3. <span id="used-material-3"></span> [Pandas Tutorial](https://www.w3schools.com/python/pandas/default.asp)

4. <span id="used-material-4"></span> [Dask DataFrame](https://docs.dask.org/en/stable/dataframe.html)

5. <span id="used-material-5"></span> [Converting Pandas Dataframe To Dask Dataframe](https://www.geeksforgeeks.org/pandas/converting-pandas-dataframe-to-dask-dataframe/)

6. <span id="used-material-6"></span> [All About Parquet Part 08 - Reading and Writing Parquet Files in Python ](https://dev.to/alexmercedcoder/all-about-parquet-part-08-reading-and-writing-parquet-files-in-python-338d)

7. <span id="used-material-7"></span> [PyArrow Pip package](https://pypi.org/project/pyarrow/)

## Why use Pandas? 

Pandas is the most common data manipulation library in Python for the following reasons:

- Most common data analysis tool across multiple domains, robust core engine, and extensive integration with other tools (mature)

- Easy-to-use declarative vector operations, automated label alignment, and unified handling of semi-structured data (abstracted)

- Handles widely supported storage formats, enables easy switching across Python tools, and created pandas code can be adapted into various big data tools (interoperable)

These features make Pandas the default data manipulation tool for data preprocessing and analysis, simplifying and abstracting away the data operations used by automation, scripts, and functions.

## How to use Pandas?

In our use case, we mostly use Pandas for simple data preprocessing, with occasionally more complex data analysis, which you can check further using |[(1)](#used-material-1), [(2)](#used-material-2), [(3)](#used-material-3)|. The common uses are the following:

- Creating a DataFrame from a list

```
metrics_rows = [
    {'latency-sec': 4.5, 'data-type': 'general'},
    {'latency-sec': 7.5, 'data-type': 'synthetic'}
]

metrics_df = pd.DataFrame(metrics_rows)
```

- Selecting a chunk from the DataFrame

```
for i in range(0, total_rows, chunk_size):
    df_chunk = pandas_df.iloc[i : i + chunk_size]
```

- Gettings stats of a column

```
min_value = metrics_df[column].min()
max_value = metrics_df[column].max()
mean_value = metrics_df[column].mean()
median_value = metrics_df[column].median()
```

- Getting stats of columns

```
general_stats_df = metrics_df[relevant_columns].agg(['mean', 'std'])
```

- Getting grouped stats of columns

```
group_stats_df = metrics_df.groupby(group_column)[relevant_columns].agg(['mean', 'std'])
```

- Getting melted grouped stats of columns

```
melted = metrics_df.melt(
    id_vars = group_columns,
    value_vars = score_columns,
    var_name = 'metric',
    value_name = 'score'
)

index_cols = group_columns + ['metric']

grouped_counts = pd.crosstab(
    index = [melted[col] for col in index_cols],
    columns = melted['score']
)

grouped_counts['pass_pct'] = (grouped_counts[1] / (grouped_counts[0] + grouped_counts[1]) * 100).round(2)
```

- Converting the dataframe into a dict

```
metrics_df.to_dict(orient = 'index')
```

- Serializing a DataFrame into object data

```
from io import BytesIO
buffer = BytesIO()
dataframe.to_parquet(buffer, index = False)
buffer.seek(0)
serialized_data = buffer.getvalue()
```

- Deserializing the object data into a DataFrame

```
from io import BytesIO
deserialized_data = BytesIO(serialized_dataframe)
restored_dataframe = pd.read_parquet(deserialized_data)
```

## Pandas DataFrame Splitting and Serialization

When storing Pandas Dataframes with amounts of rows in millions and amounts of colums over 10, there is a need for dataframe splitting and serialization to reduce memory requirements of processing and storage to enable faster object storage interactions. The solution for processing such large dataframes is to use Dask |[(4)](#used-material-4), [(5)](#used-material-5)|, while Parquet handels the serialization |[(6)](#used-material-6), [(7)](#used-material-7)|. An example of their united use is the following:

```
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
```

This example code uses Dask to collectively rename the dataframe batches that are saved as parquet with to_delayed() and compute() enabling controlled use of memory by using disk when the Pandas dataframes won't fit in the memory. For our use case this code also divides the collective data into dataframes with 20 000 rows, which enables data manipulation without needing Dask. 

---