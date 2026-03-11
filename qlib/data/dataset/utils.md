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

````markdown
# Qlib `fetch_df_by_index`

https://github.com/microsoft/qlib/blob/main/qlib/data/dataset/utils.py#L41

## Purpose

Select data from a **MultiIndex DataFrame** by specifying:

- a **selector**
- a specific **index level**

Typical use cases:

- select stocks by **date**
- select dates by **stock**
- perform **MultiIndex slicing**

---

# Source Code

```python
def fetch_df_by_index(
    df: pd.DataFrame,
    selector: Union[pd.Timestamp, slice, str, list, pd.Index],
    level: Union[str, int],
    fetch_orig=True,
) -> pd.DataFrame:

    if level is None or isinstance(selector, pd.MultiIndex):
        return df.loc(axis=0)[selector]

    idx_slc = (selector, slice(None, None))

    if get_level_index(df, level) == 1:
        idx_slc = idx_slc[1], idx_slc[0]

    if fetch_orig:
        for slc in idx_slc:
            if slc != slice(None, None):
                return df.loc[pd.IndexSlice[idx_slc],]
        else:
            return df
    else:
        return df.loc[pd.IndexSlice[idx_slc],]
````

---

# Example DataFrame

Typical Qlib dataset structure.

```python
import pandas as pd

index = pd.MultiIndex.from_tuples(
[
("2024-01-01", "AAPL"),
("2024-01-01", "MSFT"),
("2024-01-02", "AAPL"),
("2024-01-02", "MSFT"),
],
names=["datetime", "instrument"]
)

df = pd.DataFrame(
{
"close":[100,200,101,202],
"volume":[1000,1500,1200,1800]
},
index=index
)
```

Result:

```
                        close   volume
datetime   instrument
2024-01-01 AAPL           100     1000
           MSFT           200     1500
2024-01-02 AAPL           101     1200
           MSFT           202     1800
```

Index levels:

```
level 0 → datetime
level 1 → instrument
```

---

# Selector

`selector` specifies **which index values to select**.

Possible types:

```
pd.Timestamp
slice
str
list
pd.Index
pd.MultiIndex
```

Examples:

```
selector = "2024-01-01"
selector = "AAPL"
selector = slice("2024-01-01","2024-01-02")
selector = ["AAPL","MSFT"]
```

---

# Case 1: selector is MultiIndex

```python
if level is None or isinstance(selector, pd.MultiIndex):
    return df.loc(axis=0)[selector]
```

If the selector already contains **full index tuples**, no level inference is needed.

Example:

```
selector =
[
("2024-01-01","AAPL"),
("2024-01-02","MSFT")
]
```

Selection:

```
df.loc[selector]
```

Result:

```
                        close volume
datetime   instrument
2024-01-01 AAPL           100   1000
2024-01-02 MSFT           202   1800
```

---

# Constructing `idx_slc`

```python
idx_slc = (selector, slice(None))
```

This creates a **tuple for MultiIndex slicing**.

Example:

```
selector = "2024-01-01"
```

Then:

```
idx_slc = ("2024-01-01", slice(None))
```

Meaning:

```
(datetime="2024-01-01", instrument=all)
```

Equivalent to:

```
df.loc["2024-01-01", :]
```

Result:

```
           close volume
instrument
AAPL        100   1000
MSFT        200   1500
```

---

# Level Adjustment

```python
if get_level_index(df, level) == 1:
    idx_slc = idx_slc[1], idx_slc[0]
```

If the selector targets **level 1**, the tuple must be swapped.

Example:

```
selector = "AAPL"
level = "instrument"
```

Initial slice:

```
idx_slc = ("AAPL", slice(None))
```

But index order is:

```
(datetime, instrument)
```

So it becomes:

```
idx_slc = (slice(None), "AAPL")
```

Selection:

```
df.loc[:, "AAPL"]
```

Result:

```
                        close volume
datetime   instrument
2024-01-01 AAPL           100   1000
2024-01-02 AAPL           101   1200
```

---

# `pd.IndexSlice`

`pd.IndexSlice` simplifies MultiIndex slicing.

Example:

```
idx = pd.IndexSlice
df.loc[idx["2024-01-01", :]]
```

Equivalent to:

```
df.loc[("2024-01-01", slice(None))]
```

---

# `fetch_orig` Behavior

Key logic:

```python
if fetch_orig:
    for slc in idx_slc:
        if slc != slice(None, None):
            return df.loc[pd.IndexSlice[idx_slc],]
    else:
        return df
```

Meaning:

If the slice selects **all data**, return the **original DataFrame**.

Example:

```
idx_slc = (slice(None), slice(None))
```

This means:

```
select everything
```

Instead of executing:

```
df.loc[:, :]
```

which creates a **new DataFrame**, the function returns:

```
df
```

directly.

---

# Why This Optimization Exists

Qlib datasets can be very large.

Typical scale:

```
3000 stocks
×
10 years
```

Rows may exceed:

```
10,000,000+
```

If every operation performs:

```
df.loc[:, :]
```

pandas creates a **new DataFrame copy**, which wastes:

* memory
* CPU time

Therefore:

```
fetch_orig=True
```

avoids unnecessary copying by returning the original DataFrame when no filtering is applied.

```
```
