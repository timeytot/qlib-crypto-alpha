# Source: `qlib/scripts/dump_bin.py`

## `read_as_df()` Function Explanation

This note explains the `read_as_df()` helper function in `qlib/scripts/dump_bin.py`.

```python
def read_as_df(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    Read a csv or parquet file into a pandas DataFrame.
    """
    file_path = Path(file_path).expanduser()
    suffix = file_path.suffix.lower()

    keep_keys = {".csv": ("low_memory",)}
    kept_kwargs = {}
    for k in keep_keys.get(suffix, []):
        if k in kwargs:
            kept_kwargs[k] = kwargs[k]

    if suffix == ".csv":
        return pd.read_csv(file_path, **kept_kwargs)
    elif suffix == ".parquet":
        return pd.read_parquet(file_path, **kept_kwargs)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")
```

---

## 1. What this function does

This function provides a unified way to read data files into a pandas `DataFrame`.

It supports two file formats:

```text
.csv
.parquet
```

So instead of writing different code like this:

```python
df = pd.read_csv("BTCUSDT.csv")
```

or this:

```python
df = pd.read_parquet("BTCUSDT.parquet")
```

we can simply write:

```python
df = read_as_df("BTCUSDT.csv")
df = read_as_df("BTCUSDT.parquet")
```

The function checks the file suffix automatically and chooses the correct pandas reader.

---

## 2. `file_path = Path(file_path).expanduser()`

This line converts the input path into a `Path` object.

Example:

```python
file_path = "~/data/BTCUSDT.csv"
file_path = Path(file_path).expanduser()
```

After `expanduser()`, `~` is expanded to the user's home directory.

For example:

```text
~/data/BTCUSDT.csv
```

may become:

```text
/home/timeg/data/BTCUSDT.csv
```

This makes the path easier and safer to work with.

---

## 3. `suffix = file_path.suffix.lower()`

This line gets the file extension.

Example:

```python
file_path = Path("BTCUSDT.csv")
suffix = file_path.suffix.lower()
```

Result:

```python
".csv"
```

If the file is:

```python
Path("BTCUSDT.parquet")
```

then:

```python
suffix = ".parquet"
```

The `.lower()` part makes the suffix lowercase, so `.CSV` and `.csv` are treated the same.

---

## 4. What is `**kwargs`?

`**kwargs` collects extra keyword arguments passed into the function.

Example:

```python
read_as_df("BTCUSDT.csv", low_memory=False, abc=123)
```

Inside the function, `kwargs` becomes:

```python
{
    "low_memory": False,
    "abc": 123,
}
```

So `kwargs` is just a dictionary containing extra options.

---

## 5. The confusing part: `keep_keys` and `kept_kwargs`

Original code:

```python
keep_keys = {".csv": ("low_memory",)}
kept_kwargs = {}
for k in keep_keys.get(suffix, []):
    if k in kwargs:
        kept_kwargs[k] = kwargs[k]
```

This part filters `kwargs`.

### `keep_keys`

```python
keep_keys = {".csv": ("low_memory",)}
```

This means:

> For `.csv` files, only keep the `low_memory` argument.

In other words, `low_memory` is allowed for CSV files.

### `kept_kwargs`

```python
kept_kwargs = {}
```

This is the filtered version of `kwargs`.

Only allowed arguments are copied into `kept_kwargs`.

---

## 6. Equivalent beginner-friendly version

This code:

```python
keep_keys = {".csv": ("low_memory",)}
kept_kwargs = {}
for k in keep_keys.get(suffix, []):
    if k in kwargs:
        kept_kwargs[k] = kwargs[k]
```

is equivalent to this simpler version:

```python
kept_kwargs = {}

if suffix == ".csv":
    if "low_memory" in kwargs:
        kept_kwargs["low_memory"] = kwargs["low_memory"]
```

So the purpose is simple:

> Only pass safe and supported arguments to the actual pandas reader.

---

## 7. Example: CSV file

Call:

```python
df = read_as_df("BTCUSDT.csv", low_memory=False, abc=123)
```

Inside the function:

```python
suffix = ".csv"

kwargs = {
    "low_memory": False,
    "abc": 123,
}
```

Because `keep_keys` only allows `low_memory` for `.csv`, the filtered result is:

```python
kept_kwargs = {
    "low_memory": False,
}
```

Then the function runs:

```python
pd.read_csv(file_path, low_memory=False)
```

The unsupported `abc=123` is discarded.

---

## 8. Example: Parquet file

Call:

```python
df = read_as_df("BTCUSDT.parquet", low_memory=False)
```

Inside the function:

```python
suffix = ".parquet"
```

But `keep_keys` only contains `.csv`:

```python
keep_keys = {".csv": ("low_memory",)}
```

So:

```python
keep_keys.get(".parquet", [])
```

returns:

```python
[]
```

The loop does not run, and:

```python
kept_kwargs = {}
```

Then the function runs:

```python
pd.read_parquet(file_path)
```

It does not pass `low_memory=False`, because `pd.read_parquet()` does not use that argument.

---

## 9. Why filter arguments?

Different pandas readers support different arguments.

For example:

```python
pd.read_csv("BTCUSDT.csv", low_memory=False)
```

is valid.

But:

```python
pd.read_parquet("BTCUSDT.parquet", low_memory=False)
```

may raise an error, because `low_memory` is not a normal argument for `read_parquet()`.

So the function uses `keep_keys` to avoid passing unsupported arguments to the wrong reader.

---

## 10. Unsupported file format

If the file is not `.csv` or `.parquet`, the function raises an error.

Example:

```python
read_as_df("BTCUSDT.xlsx")
```

Result:

```text
ValueError: Unsupported file format: .xlsx
```

This makes the function behavior clear and prevents silent mistakes.

---

## 11. Final summary

The function is a small wrapper around pandas file readers.

Its core logic is:

```python
if suffix == ".csv":
    return pd.read_csv(file_path, **kept_kwargs)
elif suffix == ".parquet":
    return pd.read_parquet(file_path, **kept_kwargs)
else:
    raise ValueError(...)
```

The `keep_keys` / `kept_kwargs` part is only used to filter extra parameters.

A very simple mental model is:

```python
read_as_df("xxx.csv")      # uses pd.read_csv
read_as_df("xxx.parquet")  # uses pd.read_parquet
```

And:

```python
kept_kwargs = filtered kwargs
```

Only safe parameters are passed to pandas.
