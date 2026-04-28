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

建议文件名：

```text
qlib_crypto_dump_bin_pipeline_notes.md
```

下面是整理后的终极版，直接复制进 GitHub 的 `.md` 文件即可：

````markdown
# Qlib Crypto 数据导入与 `dump_bin.py` 流程笔记

Source: `qlib/scripts/dump_bin.py`

本文记录对 Qlib 数据转换脚本 `dump_bin.py` 的理解，重点是：  
如何把原始 crypto CSV / Parquet 数据转换成 Qlib 标准数据结构。

---

## 1. Qlib 标准数据结构

目标输出目录结构：

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
````

三个核心目录：

```text
calendars/    = 全局交易日历
instruments/  = 标的列表，以及每个标的的起止日期
features/     = 每个 symbol 的字段数据，保存为 .bin 文件
```

---

## 2. dump 命令示例

```bash
python dump_bin.py dump_all \
  --data_path raw_data/1d_nor \
  --qlib_dir qlib_data \
  --freq day \
  --file_suffix .csv
```

含义：

```text
从 raw_data/1d_nor 读取原始 csv
转换后写入 qlib_data
```

其中：

```text
data_path = 原始数据入口
qlib_dir  = Qlib 标准数据输出目录
```

---

## 3. `exclude_fields` / `include_fields` 的清洗

代码：

```python
self._exclude_fields = tuple(filter(lambda x: len(x) > 0, map(str.strip, exclude_fields)))
self._include_fields = tuple(filter(lambda x: len(x) > 0, map(str.strip, include_fields)))
```

作用：

```text
把用户传入的字段列表清洗干净：
1. 去掉前后空格
2. 删除空字符串
3. 转成 tuple
```

例如：

```python
exclude_fields = "symbol, date, "
```

先变成：

```python
["symbol", " date", " "]
```

清洗后：

```python
("symbol", "date")
```

---

## 4. `self.df_files`：统一获得待处理文件列表

代码：

```python
self.df_files = sorted(data_path.glob(f"*{self.file_suffix}") if data_path.is_dir() else [data_path])
```

作用：

```text
如果 data_path 是目录，就找出目录下所有指定后缀文件；
如果 data_path 是单个文件，就直接把它放进列表。
```

例如：

```text
raw_data/1d_nor/
├── BTCUSDT.csv
├── ETHUSDT.csv
└── SOLUSDT.csv
```

则：

```python
self.df_files
```

结果类似：

```python
[
    Path("BTCUSDT.csv"),
    Path("ETHUSDT.csv"),
    Path("SOLUSDT.csv"),
]
```

这样后面代码就可以统一循环处理：

```python
for file_path in self.df_files:
    ...
```

---

## 5. `instruments/all.txt` 的结构

`instruments/all.txt` 内容类似：

```text
BTCUSDT	2023-01-01	2026-04-01
ETHUSDT	2023-01-01	2026-04-01
SOLUSDT	2023-01-01	2026-04-01
```

三列含义：

```text
symbol          = 标的代码
start_datetime  = 最早有数据的日期
end_datetime    = 最后有数据的日期
```

中间用 tab 分隔：

```python
INSTRUMENTS_SEP = "\t"
```

---

## 6. `_read_instruments()`：读取已有 instruments 文件

代码：

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

作用：

```text
读取 qlib_data/instruments/all.txt，并手动指定列名。
```

因为 `all.txt` 保存时没有 header，所以读回来必须加：

```python
names=["symbol", "start_datetime", "end_datetime"]
```

否则 pandas 不知道这三列分别叫什么。

---

## 7. `get_symbol_from_file()`：从文件名提取 symbol

代码：

```python
def get_symbol_from_file(self, file_path: Path) -> str:
    return fname_to_code(file_path.stem.strip().lower())
```

作用：

```text
从文件名里提取 symbol。
```

例如：

```text
BTCUSDT.csv -> btcusdt
ETHUSDT.csv -> ethusdt
SOLUSDT.csv -> solusdt
```

其中：

```python
file_path.stem
```

表示：

```text
文件名去掉后缀
```

例如：

```text
BTCUSDT.csv -> BTCUSDT
```

---

## 8. `data_merge_calendar()`：按全局 calendar 对齐单个 symbol 数据

代码：

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

核心作用：

```text
把单个 symbol 的行情 df，按全局 Qlib calendar 对齐。
```

例如全局 calendar：

```text
2025-01-01
2025-01-02
2025-01-03
```

原始 BTC 数据缺了 `2025-01-02`：

```text
date        close
2025-01-01  100
2025-01-03  120
```

对齐后：

```text
date        close
2025-01-01  100
2025-01-02  NaN
2025-01-03  120
```

意义：

```text
保证所有 symbol 都按照同一套 calendar 的位置写入 bin。
```

---

## 9. Qlib `.bin` 文件结构

第一次全量写入时：

```python
np.hstack([date_index, _df[field]]).astype("<f").tofile(...)
```

写入内容类似：

```text
[date_index, value1, value2, value3, ...]
```

例如：

```text
[2.0, 100.0, 110.0, 120.0]
```

含义：

```text
2.0      = 当前 symbol 的第一条数据从全局 calendar 的第 2 个位置开始
100.0    = 第一个 close 值
110.0    = 第二个 close 值
120.0    = 第三个 close 值
```

也就是说：

```text
bin 文件第一个值不是行情值，而是 date_index。
后面的值才是真正的字段数据。
```

---

## 10. update 模式 / 文件已存在

代码：

```python
with bin_path.open("ab") as fp:
    np.array(_df[field]).astype("<f").tofile(fp)
```

其中：

```text
ab = append binary
```

意思是：

```text
以二进制追加模式打开文件。
```

update 时只追加新数据，不再写 `date_index`。

原因：

```text
旧 .bin 文件开头已经有 date_index。
增量更新时如果再写一次 date_index，文件结构就错了。
```

---

## 11. `date_range_list.append(...)` 的作用

代码：

```python
date_range_list.append(f"{self.INSTRUMENTS_SEP.join(_inst_fields)}")
```

假设：

```python
_inst_fields = ["BTCUSDT", "2023-01-01", "2026-04-01"]
```

则：

```python
"\t".join(_inst_fields)
```

得到：

```text
BTCUSDT	2023-01-01	2026-04-01
```

加入 `date_range_list` 后，最后写入：

```text
qlib_data/instruments/all.txt
```

也就是 instruments 文件中的一行。

---

## 12. `dump_all` 全量流程

整体流程：

```text
_dump_all
    │
    ├─ _get_all_date()
    │     ├─ 扫描所有 csv/parquet
    │     ├─ 收集所有日期
    │     └─ 收集每个 symbol 的起止日期
    │
    ├─ _dump_calendars()
    │     └─ 生成 calendars/day.txt
    │
    ├─ _dump_instruments()
    │     └─ 生成 instruments/all.txt
    │
    └─ _dump_features()
          ├─ 遍历每个 symbol 文件
          ├─ 读取完整行情 df
          ├─ 按 calendar 对齐
          └─ 每个字段写成 .bin
```

---

## 13. 单个 symbol 写入 features 的核心链路

单个文件，例如：

```text
BTCUSDT.csv
```

处理过程：

```text
BTCUSDT.csv
    ↓
读取成 DataFrame
    ↓
提取 code = btcusdt
    ↓
删除重复 date
    ↓
创建 features/btcusdt/
    ↓
按照全局 calendar 对齐
    ↓
计算 date_index
    ↓
遍历字段 open/high/low/close/volume
    ↓
每个字段写成一个 .bin
```

最终生成：

```text
qlib_data/features/btcusdt/open.day.bin
qlib_data/features/btcusdt/high.day.bin
qlib_data/features/btcusdt/low.day.bin
qlib_data/features/btcusdt/close.day.bin
qlib_data/features/btcusdt/volume.day.bin
```

---

## 14. 最终理解

`dump_bin.py` 的核心作用：

```text
把原始 CSV / Parquet 行情数据，
转换成 Qlib 标准的 calendars + instruments + features/*.bin 结构。
```

主链路可以压缩成：

```text
raw_data/*.csv
    ↓
扫描文件列表
    ↓
生成全局 calendar
    ↓
生成 instruments/all.txt
    ↓
逐个 symbol 读取行情数据
    ↓
按全局 calendar 对齐
    ↓
每个字段写成 .bin
    ↓
qlib_data/
```

最终 Qlib 就可以通过：

```python
D.features(...)
```

读取这些 crypto 数据。

```
```
