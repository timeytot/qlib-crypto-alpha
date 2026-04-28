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

# qlib_crypto_dump_bin_pipeline_notes

Source: `qlib/scripts/dump_bin.py`

This note summarizes the data conversion pipeline in Qlib's `dump_bin.py`.

The key question is:

> How does Qlib convert raw crypto CSV / Parquet data into the standard Qlib data structure?

The final Qlib data directory looks like this:

```text
qlib_data/
├── calendars/
│   └── day.txt
├── instruments/
│   └── all.txt
└── features/
    ├── btcusdt/
    │   ├── open.day.bin
    │   ├── high.day.bin
    │   ├── low.day.bin
    │   ├── close.day.bin
    │   └── volume.day.bin
    └── ethusdt/
        ├── open.day.bin
        ├── close.day.bin
        └── volume.day.bin
```

---

## 1. Example dump command

```bash
python dump_bin.py dump_all \
  --data_path raw_data/1d_nor \
  --qlib_dir qlib_data \
  --freq day \
  --file_suffix .csv
```

Meaning:

```text
Read raw CSV files from raw_data/1d_nor
Convert them into Qlib format
Write the output into qlib_data
```

The key distinction is:

```text
data_path = input path for raw data
qlib_dir  = output path for Qlib standard data
```

---

## 2. Cleaning `exclude_fields` / `include_fields`

Code:

```python
self._exclude_fields = tuple(filter(lambda x: len(x) > 0, map(str.strip, exclude_fields)))
self._include_fields = tuple(filter(lambda x: len(x) > 0, map(str.strip, include_fields)))
```

Purpose:

```text
Clean the user-provided field list:
1. Remove leading and trailing spaces
2. Remove empty strings
3. Convert the result into a tuple
```

Example:

```python
exclude_fields = "symbol, date, "
```

After splitting:

```python
["symbol", " date", " "]
```

After cleaning:

```python
("symbol", "date")
```

---

## 3. `self.df_files`: getting the list of files to process

Code:

```python
self.df_files = sorted(data_path.glob(f"*{self.file_suffix}") if data_path.is_dir() else [data_path])
```

Purpose:

```text
If data_path is a directory, find all files with the specified suffix.
If data_path is a single file, put that file directly into a list.
```

Example:

```text
raw_data/1d_nor/
├── BTCUSDT.csv
├── ETHUSDT.csv
└── SOLUSDT.csv
```

Then:

```python
self.df_files
```

will be similar to:

```python
[
    Path("BTCUSDT.csv"),
    Path("ETHUSDT.csv"),
    Path("SOLUSDT.csv"),
]
```

This allows the later code to process everything in one unified loop:

```python
for file_path in self.df_files:
    ...
```

---

## 4. Structure of `instruments/all.txt`

The `instruments/all.txt` file looks like this:

```text
BTCUSDT	2023-01-01	2026-04-01
ETHUSDT	2023-01-01	2026-04-01
SOLUSDT	2023-01-01	2026-04-01
```

The three columns mean:

```text
symbol          = instrument code
start_datetime  = first available date for this instrument
end_datetime    = last available date for this instrument
```

The separator is a tab:

```python
INSTRUMENTS_SEP = "\t"
```

---

## 5. `_read_instruments()`: reading an existing instruments file

Code:

```python
def _read_instruments(self, instrument_path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        instrument_path,
        sep=self.INSTRUMENTS_SEP,
        names=[
            self.symbol_field_name,
            self.INSTRUMENTS_START_FIELD,
            self.INSTRUMENTS_END_FIELD,
        ],
    )
    return df
```

Purpose:

```text
Read qlib_data/instruments/all.txt and manually assign column names.
```

Because `all.txt` is saved without a header, pandas needs explicit column names:

```python
names=["symbol", "start_datetime", "end_datetime"]
```

Otherwise pandas would not know what the three columns represent.

---

## 6. `get_symbol_from_file()`: extracting symbol from filename

Code:

```python
def get_symbol_from_file(self, file_path: Path) -> str:
    return fname_to_code(file_path.stem.strip().lower())
```

Purpose:

```text
Extract the symbol from the filename.
```

Examples:

```text
BTCUSDT.csv -> btcusdt
ETHUSDT.csv -> ethusdt
SOLUSDT.csv -> solusdt
```

Here:

```python
file_path.stem
```

means:

```text
Filename without extension
```

Example:

```text
BTCUSDT.csv -> BTCUSDT
```

---

## 7. `data_merge_calendar()`: aligning one symbol to the global calendar

Code:

```python
def data_merge_calendar(self, df: pd.DataFrame, calendars_list: List[pd.Timestamp]) -> pd.DataFrame:
    calendars_df = pd.DataFrame(data=calendars_list, columns=[self.date_field_name])
    calendars_df[self.date_field_name] = calendars_df[self.date_field_name].astype("datetime64[ns]")

    cal_df = calendars_df[
        (calendars_df[self.date_field_name] >= df[self.date_field_name].min())
        & (calendars_df[self.date_field_name] <= df[self.date_field_name].max())
    ]

    cal_df.set_index(self.date_field_name, inplace=True)
    df.set_index(self.date_field_name, inplace=True)

    r_df = df.reindex(cal_df.index)
    return r_df
```

Core purpose:

```text
Align a single symbol's DataFrame to the global Qlib calendar.
```

Example global calendar:

```text
2025-01-01
2025-01-02
2025-01-03
```

Original BTC data is missing `2025-01-02`:

```text
date        close
2025-01-01  100
2025-01-03  120
```

After alignment:

```text
date        close
2025-01-01  100
2025-01-02  NaN
2025-01-03  120
```

Meaning:

```text
All symbols are aligned to the same calendar positions before being written into .bin files.
```

---

## 8. Qlib `.bin` file structure

During the first full dump, the code writes data like this:

```python
np.hstack([date_index, _df[field]]).astype("<f").tofile(...)
```

The written content is conceptually:

```text
[date_index, value1, value2, value3, ...]
```

Example:

```text
[2.0, 100.0, 110.0, 120.0]
```

Meaning:

```text
2.0      = the first data point of this symbol starts from position 2 in the global calendar
100.0    = first close value
110.0    = second close value
120.0    = third close value
```

In other words:

```text
The first value in a .bin file is not a market value.
It is the date_index.
The remaining values are the actual field data.
```

---

## 9. Update mode / existing `.bin` file

Code:

```python
with bin_path.open("ab") as fp:
    np.array(_df[field]).astype("<f").tofile(fp)
```

Here:

```text
ab = append binary
```

Meaning:

```text
Open the file in binary append mode.
```

In update mode, Qlib only appends new values.

It does not write `date_index` again.

Reason:

```text
The existing .bin file already has date_index at the beginning.
If date_index were written again during an update, the file structure would become invalid.
```

---

## 10. Purpose of `date_range_list.append(...)`

Code:

```python
date_range_list.append(f"{self.INSTRUMENTS_SEP.join(_inst_fields)}")
```

Assume:

```python
_inst_fields = ["BTCUSDT", "2023-01-01", "2026-04-01"]
```

Then:

```python
"\t".join(_inst_fields)
```

returns:

```text
BTCUSDT	2023-01-01	2026-04-01
```

After being appended to `date_range_list`, this line will eventually be written into:

```text
qlib_data/instruments/all.txt
```

It becomes one row in the instruments file.

---

## 11. Full `dump_all` pipeline

Overall flow:

```text
_dump_all
    │
    ├─ _get_all_date()
    │     ├─ Scan all csv/parquet files
    │     ├─ Collect all dates
    │     └─ Collect start/end date for each symbol
    │
    ├─ _dump_calendars()
    │     └─ Generate calendars/day.txt
    │
    ├─ _dump_instruments()
    │     └─ Generate instruments/all.txt
    │
    └─ _dump_features()
          ├─ Iterate through each symbol file
          ├─ Read full market data DataFrame
          ├─ Align data to the global calendar
          └─ Write each field into a .bin file
```

---

## 12. Core chain for writing features of one symbol

For one file, such as:

```text
BTCUSDT.csv
```

The processing flow is:

```text
BTCUSDT.csv
    ↓
Read into DataFrame
    ↓
Extract code = btcusdt
    ↓
Drop duplicate dates
    ↓
Create features/btcusdt/
    ↓
Align to the global calendar
    ↓
Calculate date_index
    ↓
Iterate through fields: open/high/low/close/volume
    ↓
Write each field into a separate .bin file
```

Final output:

```text
qlib_data/features/btcusdt/open.day.bin
qlib_data/features/btcusdt/high.day.bin
qlib_data/features/btcusdt/low.day.bin
qlib_data/features/btcusdt/close.day.bin
qlib_data/features/btcusdt/volume.day.bin
```

---

## 13. Final understanding

The core role of `dump_bin.py` is:

```text
Convert raw CSV / Parquet market data
into Qlib's standard calendars + instruments + features/*.bin structure.
```

The main pipeline can be summarized as:

```text
raw_data/*.csv
    ↓
Scan file list
    ↓
Generate global calendar
    ↓
Generate instruments/all.txt
    ↓
Read market data symbol by symbol
    ↓
Align each symbol to the global calendar
    ↓
Write each field into .bin files
    ↓
qlib_data/
```

After this conversion, Qlib can read the crypto data through:

```python
D.features(...)
```
