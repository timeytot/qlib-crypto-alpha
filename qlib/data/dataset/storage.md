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

## Design Trade-off Summary

`HashingStockStorage` optimizes for the **90% use case** (stock-wise queries) at the cost of the **10% use case** (cross-sectional, time-wise queries). This aligns with typical quantitative research workflows where analyzing individual stock time series is the most frequent operation.
