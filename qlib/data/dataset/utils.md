# `fetch_df_by_col` Function

**Source Code URL**: https://github.com/microsoft/qlib/blob/main/qlib/data/dataset/utils.py#L81

```python
def fetch_df_by_col(df: pd.DataFrame, col_set: Union[str, List[str]]) -> pd.DataFrame:
    from .handler import DataHandler  # pylint: disable=C0415

    if not isinstance(df.columns, pd.MultiIndex) or col_set == DataHandler.CS_RAW:
        return df
    elif col_set == DataHandler.CS_ALL:
        return df.droplevel(axis=1, level=0)
    else:
        return df.loc(axis=1)[col_set]
```

## Sample DataFrame with MultiIndex Columns

```python
import pandas as pd
import numpy as np

# Create MultiIndex columns
columns = pd.MultiIndex.from_tuples([
    ('feature', 'close'), ('feature', 'volume'), ('feature', 'high'), ('feature', 'low'),
    ('label', 'LABEL0'), ('label', 'LABEL1'),
    ('meta', 'stock_name')
], names=['group', 'field'])

# Create MultiIndex rows
iterables = [['2020-01-02', '2020-01-03', '2020-01-04'], ['SH600000', 'SH600001']]
index = pd.MultiIndex.from_product(iterables, names=['datetime', 'instrument'])

# Create data
np.random.seed(42)
data = np.random.randn(len(index), len(columns))
df = pd.DataFrame(data, index=index, columns=columns)
```

Original DataFrame:
```
group                      feature                           label                 meta
field                        close     volume      high       low   LABEL0   LABEL1 stock_name
datetime   instrument
2020-01-02 SH600000       0.496714  0.647689  0.963663  0.156019  0.155995 -0.334885   0.496714
           SH600001      -1.130262  0.358996 -1.026403 -0.476184 -0.705672 -1.061593  -1.130262
2020-01-03 SH600000       0.513128  0.666383  0.105908  0.130892 -0.321222 -0.156475   0.513128
           SH600001       0.205048  1.054451  0.276256 -0.731278  0.105427  0.642476   0.205048
2020-01-04 SH600000       0.895467  0.386345  0.510618  0.542560  0.238923  0.372832   0.895467
           SH600001      -0.161233  0.492150  0.317508 -1.054119 -0.328407  0.658182  -0.161233
```

## Examples

### Example 1: Single-level columns
```python
df_single = pd.DataFrame({'close': [1,2,3], 'volume': [100,200,300]}, 
                         index=['2020-01-02','2020-01-03','2020-01-04'])
result = fetch_df_by_col(df_single, DataHandler.CS_ALL)
print(result is df_single)  # True - returns original df
```

### Example 2: `col_set = DataHandler.CS_RAW`
```python
result = fetch_df_by_col(df, DataHandler.CS_RAW)
print(result is df)  # True - returns original df
```

### Example 3: `col_set = DataHandler.CS_ALL`
```python
result = fetch_df_by_col(df, DataHandler.CS_ALL)
print(result.columns)  # Index(['close', 'volume', 'high', 'low', 'LABEL0', 'LABEL1', 'stock_name'])
```

### Example 4: Select specific groups
```python
result = fetch_df_by_col(df, ['feature', 'label'])
# Returns MultiIndex columns with only 'feature' and 'label' groups
```

### Example 5: Select single group
```python
result = fetch_df_by_col(df, ['meta'])
# Returns MultiIndex columns with only 'meta' group
```
