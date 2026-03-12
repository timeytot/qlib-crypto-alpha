# `HashingStockStorage` 

**Source Code**: https://github.com/microsoft/qlib/blob/main/qlib/data/dataset/storage.py#L88

## Core Concept: Stock-First Design

`HashingStockStorage` is optimized for **stock-wise queries**. Time filtering is a secondary, "pass-through" feature.

### Scenario 1: Primary Task - Select Stocks (No Time Filter)

```python
# Best at: selecting stocks, no time constraints
selector = "AAPL"
level = "instrument"

stock_dict, time_sel = storage._fetch_hash_df_by_stock(selector, level)
# stock_dict = {"AAPL": aapl_data}  # O(1) hash lookup
# time_sel = slice(None)  # No time filtering (all time)
```

### Scenario 2: Secondary Task - Select Stocks + Time Filter

```python
# Can also handle: select stocks with time constraints
selector = ("2024-01-01", "AAPL")  # tuple (time, stock)
level = None

stock_dict, time_sel = storage._fetch_hash_df_by_stock(selector, level)
# stock_dict = {"AAPL": aapl_data}  # Still O(1) for stock
# time_sel = "2024-01-01"  # Time selector extracted as a "sidecar"
```

### Scenario 3: Not Optimized - Select Time Only

```python
# Not optimized: time-only queries (all stocks)
selector = slice("2024-01-01", "2024-01-31")
level = "datetime"

stock_dict, time_sel = storage._fetch_hash_df_by_stock(selector, level)
# stock_dict = ALL stocks  # Must return everything, filtering happens later
# time_sel = slice(None)  # Time selector from input is NOT utilized here
```

## Performance Comparison

| Query Type | `HashingStockStorage` | Plain DataFrame |
|------------|----------------------|------------------|
| Single stock, all time | **O(1)** direct lookup | O(n) full scan |
| Single stock, single day | **O(1) + index** | O(n) + index |
| Multiple stocks, all time | O(k) where k = number of stocks | O(n) |
| **All stocks, single day** | **O(k) iterate all stocks** | **O(log n) time index** |
| All stocks, time range | **O(k * log m)** | **O(log n + k)** |

## Why is `HashingStockStorage` Slower for "All Stocks" Queries?

### Data Scale Assumptions

```python
# Assume:
# - 3,000 stocks
# - 10 years of data (~2,500 trading days)
# - Total rows = 3,000 × 2,500 = 7,500,000 rows

# HashingStockStorage structure
hash_storage = {
    "SH600000": DataFrame(2500 rows),  # Stock 1 time series
    "SH600001": DataFrame(2500 rows),  # Stock 2 time series
    "SH600002": DataFrame(2500 rows),  # Stock 3 time series
    ... (3,000 such DataFrames)
}

# Plain DataFrame structure
df = pd.DataFrame(
    index=MultiIndex.from_product(
        [dates, stocks]  # Cartesian product of all dates and stocks
    )
)  # A single 7,500,000-row table
```

### Query: All Stocks on a Single Day

#### 1. `HashingStockStorage` Process

```python
def get_all_stocks_on_date(storage, target_date="2024-01-01"):
    result = {}
    
    # Must iterate through all 3,000 stocks
    for stock_id, stock_df in storage.hash_df.items():  # O(k) loop
        # For each stock, find the target date in its time series
        daily_data = stock_df.loc[target_date]  # O(log m) index lookup
        result[stock_id] = daily_data
    
    return pd.DataFrame(result).T

# Time Complexity: O(k × log m)
# = 3,000 × log(2,500) ≈ 3,000 × 12 = 36,000 operations
```

#### 2. Plain DataFrame Process

```python
def get_all_stocks_on_date(df, target_date="2024-01-01"):
    # Leverage pandas' MultiIndex directly
    # Index is (datetime, instrument), filter by datetime first
    result = df.loc[target_date]  # O(log n) direct location
    
    # One operation gets all 3,000 stocks
    return result

# Time Complexity: O(log n)
# = log(7,500,000) ≈ 23 operations
```

## Why the Huge Difference?

### `HashingStockStorage` Weakness
```python
# Like searching 3,000 different folders for one file each
for stock in stocks:          # Loop 3,000 times
    data = stock_folder.loc[date]  # Index lookup each time
```

### Plain DataFrame Strength
```python
# Like a single large table partitioned by date
# Locate the date partition once, get all stocks
data = big_table.loc[date]  # 1 operation
```

## Performance Numbers

Assume:
- k = 3,000 (number of stocks)
- n = 7.5M (total rows)
- m = 2,500 (rows per stock)
- log₂(2,500) ≈ 12

| Operation | `HashingStockStorage` | Plain DataFrame |
|-----------|----------------------|------------------|
| Single stock all time | 1 lookup | Scan 7.5M rows |
| Single stock single day | 1 lookup + 1 index | Scan 7.5M rows + index |
| **All stocks single day** | **3,000 × 12 = 36,000 ops** | **log(7.5M) ≈ 23 ops** |
| All stocks time range | 3,000 × range_size × 12 | log(7.5M) + sequential read |

# `HashingStockStorage._fetch_hash_df_by_stock` Selector Parsing Logic

**Source Code**: https://github.com/microsoft/qlib/blob/main/qlib/data/dataset/storage.py#L88

## Overview

The `_fetch_hash_df_by_stock` method parses user queries to extract **stock selectors** and **time selectors** based on the `level` parameter and `selector` type.

---

## Case 1: `level is None` (Auto-detect Mode)

When the user does not specify a level, the system automatically infers intent from the `selector` type and stock position.

### Subcase 1.1: Tuple Format (Full MultiIndex)

```python
if isinstance(selector, tuple) and self.stock_level < len(selector):
    # full selector format
    stock_selector = selector[self.stock_level]
    time_selector = selector[1 - self.stock_level]
```

**Conditions**:
- `isinstance(selector, tuple)`: Selector is a tuple
- `self.stock_level < len(selector)`: Stock level position exists in tuple

**Core Formula**:
- `stock_selector = selector[self.stock_level]`: Extract stock part
- `time_selector = selector[1 - self.stock_level]`: Extract time part (using `1 - stock_level` to auto-locate the other level)

#### Example 1: Stock at Second Level (Qlib Default)

```python
# Index order: (datetime, instrument)
self.stock_level = 1  # stock at level 1

selector = ("2024-01-01", "AAPL")  # (time, stock)

# Conditions met: isinstance(tuple) ✓, stock_level(1) < len(2) ✓
stock_selector = selector[1]  # "AAPL"
time_selector = selector[0]   # "2024-01-01" (1-1=0)

# Result: stock="AAPL", time="2024-01-01"
```

#### Example 2: Stock at First Level

```python
# Index order: (instrument, datetime)
self.stock_level = 0  # stock at level 0

selector = ("AAPL", "2024-01-01")  # (stock, time)

# Conditions met: isinstance(tuple) ✓, stock_level(0) < len(2) ✓
stock_selector = selector[0]  # "AAPL"
time_selector = selector[1]   # "2024-01-01" (1-0=1)

# Result: stock="AAPL", time="2024-01-01"
```

#### Example 3: Partial Index (Stock Only)

```python
# Stock at second level
self.stock_level = 1
selector = ("AAPL",)  # single element tuple

# Condition: stock_level(1) < len(1) ? False
# Does NOT enter this branch
```

### Subcase 1.2: List/String Format (Only When Stock at First Level)

```python
elif isinstance(selector, (list, str)) and self.stock_level == 0:
    # only stock selector
    stock_selector = selector
```

**Conditions**:
- `isinstance(selector, (list, str))`: Selector is list or string
- `self.stock_level == 0`: Stock must be at first level

#### Example 4: Stock at First Level, String Selector

```python
# Index order: (instrument, datetime)
self.stock_level = 0  # stock at level 0

selector = "AAPL"  # string

# Conditions met: isinstance(str) ✓, stock_level == 0 ✓
stock_selector = "AAPL"  # directly used as stock selector
# time_selector remains default slice(None)

# Result: stock="AAPL", time=all
```

#### Example 5: Stock at First Level, List Selector

```python
# Index order: (instrument, datetime)
self.stock_level = 0

selector = ["AAPL", "MSFT", "GOOG"]  # stock list

# Conditions met: isinstance(list) ✓, stock_level == 0 ✓
stock_selector = ["AAPL", "MSFT", "GOOG"]  # directly used as stock selector
# time_selector remains slice(None)

# Result: stock=["AAPL","MSFT","GOOG"], time=all
```

#### Example 6: Stock at Second Level, String Selector (Does Not Enter)

```python
# Index order: (datetime, instrument)
self.stock_level = 1  # stock at level 1

selector = "AAPL"  # looks like a stock

# Condition: stock_level == 0 ? False
# Does NOT enter this branch (needs other logic)
```

---

## Case 2: `level in ("instrument", self.stock_level)` (Explicit Stock Level)

When the user explicitly specifies selecting by stock level.

### Subcase 2.1: Tuple Format (Should Not Happen)

```python
if isinstance(selector, tuple):
    # NOTE: How could the stock level selector be a tuple?
    stock_selector = selector[0]
    raise TypeError(
        "I forget why would this case appear. But I think it does not make sense. So we raise a error for that case."
    )
```

**Why Error?**
- When `level="instrument"` is explicitly set, the selector should be a stock code (string) or stock list
- Passing a tuple is contradictory: tuples are for specifying multiple levels simultaneously

#### Example 7: Incorrect Usage

```python
level = "instrument"
selector = ("AAPL", "2024-01-01")  # ❌ Why pass time when explicitly selecting by stock?

# Triggers TypeError
# Error: Specifying stock level but passing tuple is不合理
```

### Subcase 2.2: List/String Format (Correct Usage)

```python
elif isinstance(selector, (list, str)):
    stock_selector = selector
```

**Direct Assignment**: The selector IS the stock selector

#### Example 8: Explicit Stock Selection with String

```python
level = "instrument"
selector = "AAPL"  # Explicit: I want stock AAPL

# Condition met: isinstance(str) ✓
stock_selector = "AAPL"
# time_selector remains slice(None)
```

#### Example 9: Explicit Stock Selection with List

```python
level = "instrument"
selector = ["AAPL", "MSFT", "GOOG"]  # Explicit: I want these stocks

# Condition met: isinstance(list) ✓
stock_selector = ["AAPL", "MSFT", "GOOG"]
# time_selector remains slice(None)
```

#### Example 10: Works Regardless of Stock Level

```python
# Works whether stock is at level 0 or 1
self.stock_level = 0  # or 1, doesn't matter
level = "instrument"
selector = "AAPL"

# Always enters this branch
stock_selector = "AAPL"  # correctly identified as stock
```

---

## Summary of Parsing Logic

| Input Pattern | Stock Position | Level Parameter | Result |
|--------------|----------------|-----------------|--------|
| `("2024-01-01", "AAPL")` | Level 1 | `None` | stock="AAPL", time="2024-01-01" |
| `("AAPL", "2024-01-01")` | Level 0 | `None` | stock="AAPL", time="2024-01-01" |
| `"AAPL"` | Level 0 | `None` | stock="AAPL", time=all |
| `["AAPL", "MSFT"]` | Level 0 | `None` | stock=["AAPL","MSFT"], time=all |
| `"AAPL"` | Level 1 | `None` | No match → returns all stocks |
| `"AAPL"` | Any | `"instrument"` | stock="AAPL", time=all |
| `("AAPL", "2024-01-01")` | Any | `"instrument"` | ❌ TypeError |

## Design Trade-off Summary

`HashingStockStorage` optimizes for the **90% use case** (stock-wise queries) at the cost of the **10% use case** (cross-sectional, time-wise queries). This aligns with typical quantitative research workflows where analyzing individual stock time series is the most frequent operation.
