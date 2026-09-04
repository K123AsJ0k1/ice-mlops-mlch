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

## Why use Pandas? 

Pandas is the most common data manipulation library in Python for the following reasons:

- Most common data analysis tool across multiple domains, robust core engine, and extensive integration with other tools (mature)

- Easy-to-use declarative vector operations, automated label alignment, and unified handling of semi-structured data (abstracted)

- Handles widely supported storage formats, enables easy switching across Python tools, and created pandas code can be adapted into various big data tools (interoperable)

These features make Pandas the default data manipulation tool for data preprocessing and analysis, simplifying and abstracting away the data operations used by automation, scripts, and functions.

## How to use Pandas?

In our use case, we mostly use Pandas for simple data preprocessing, with occasionally more complex data analysis, which you can check further using |(1), (2), (3)|. The common uses are the following:

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

---