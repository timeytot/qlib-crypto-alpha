# Deep Dive: Understanding the GroupBy Operation in Qlib's Monthly Risk Analysis

**Source Code Reference**: [https://github.com/microsoft/qlib/blob/main/qlib/contrib/report/analysis_position/risk_analysis.py#L66](https://github.com/microsoft/qlib/blob/main/qlib/contrib/report/analysis_position/risk_analysis.py#L66)

This analysis covers critical lines of code that form the foundation of the monthly risk analysis pipeline: creating the groupby object, extracting group keys for iteration, calculating month-end dates, and aggregating monthly results.

---

## Part 1: Creating the GroupBy Object

```python
report_normal_gp = report_normal_df.groupby(
    [report_normal_df.index.year, report_normal_df.index.month], 
    group_keys=False
)
```

### 1.1 Code Structure Breakdown

#### Left Side: `report_normal_gp`
- This is a **DataFrameGroupBy object**
- It doesn't perform immediate computation, but rather "remembers" how the data should be grouped
- You can later:
  - Extract specific groups with `.get_group()`
  - Apply aggregations with `.size()`, `.mean()`, etc.
  - Transform or filter grouped data

#### Right Side: Three Critical Components

##### **Part 1: The Data Being Grouped - `report_normal_df`**

```python
# Structure of report_normal_df
            return      cost        bench       turnover
date                    
2017-01-04  0.003421    0.000864    0.011693    0.576325
2017-01-05  0.000508    0.000447    0.000721    0.227882
2017-01-06  -0.003321   0.000212    -0.004322   0.102765
2017-01-09  0.006753    0.000212    0.006874    0.105864
2017-01-10  -0.000416   0.000440    -0.003350   0.208396
...         ...         ...         ...         ...
```

Key characteristics:
- Index is a **DatetimeIndex** with daily frequency
- Columns contain daily trading metrics:
  - `return`: Strategy return
  - `cost`: Transaction cost
  - `bench`: Benchmark return
  - `turnover`: Portfolio turnover rate

##### **Part 2: The Group Keys**

```python
[report_normal_df.index.year, report_normal_df.index.month]
```

This creates a **list of two Series**:

```python
# Extracted year from the index
report_normal_df.index.year
# Int64Index([2017, 2017, 2017, 2017, 2017, ...], dtype='int64', name='date')

# Extracted month from the index  
report_normal_df.index.month
# Int64Index([1, 1, 1, 1, 1, ...], dtype='int64', name='date')
```

**What Pandas does with these keys:**
1. Aligns both Series (they share the same index)
2. Uses the **combination** `(year, month)` as the grouping key
3. Each row is assigned to a group based on its date's year and month

##### **Part 3: `group_keys=False`**

This parameter controls whether group keys appear in the output index (as explained in detail below).

### 1.2 Visualization of the Grouping Process

```python
# Original data (showing only date and return)
date        return    year  month  (group key)
2017-01-04  0.003421  2017  1    ──┐
2017-01-05  0.000508  2017  1      │ Group 1: (2017,1)
2017-01-06  -0.003321 2017  1      │
2017-01-09  0.006753  2017  1      │
2017-01-10  -0.000416 2017  1      │
...         ...       ...  ...    ──┘
2017-02-01  0.002345  2017  2    ──┐
2017-02-02  -0.001234 2017  2      │ Group 2: (2017,2)
2017-02-03  0.003456  2017  2      │
...         ...       ...  ...    ──┘
2017-03-01  0.004567  2017  3    ──┐
2017-03-02  -0.002345 2017  3      │ Group 3: (2017,3)
...         ...       ...  ...    ──┘
```

### 1.3 Internal Structure of the GroupBy Object

After creation, the groupby object has this logical structure in memory:

```python
report_normal_gp = {
    (2017, 1): DataFrame([
        [2017-01-04, 0.003421, 0.000864, 0.011693, 0.576325],
        [2017-01-05, 0.000508, 0.000447, 0.000721, 0.227882],
        [2017-01-06, -0.003321, 0.000212, -0.004322, 0.102765],
        ...  # All 20 trading days in January
    ]),
    
    (2017, 2): DataFrame([
        [2017-02-01, 0.002345, 0.000567, 0.001234, 0.345678],
        [2017-02-02, -0.001234, 0.000345, -0.002345, 0.234567],
        ...  # All 19 trading days in February
    ]),
    
    (2017, 3): DataFrame([
        [2017-03-01, 0.004567, 0.000678, 0.003456, 0.456789],
        ...  # All 23 trading days in March
    ]),
    
    ...  # Other months
}
```

### 1.4 The Critical Role of `group_keys=False`

#### Without `group_keys=False` (Default Behavior)

```python
# Default group_keys=True
report_normal_gp = report_normal_df.groupby(
    [report_normal_df.index.year, report_normal_df.index.month]
)

# When retrieving data with get_group():
_m_report_normal = report_normal_gp.get_group((2017, 1))
print(_m_report_normal.index)
```

Output becomes:
```python
MultiIndex([(2017-01-04, 2017, 1),
            (2017-01-05, 2017, 1),
            (2017-01-06, 2017, 1),
            ...],
           names=['date', 'year', 'month'])
```

**The Problem**: The index becomes a **triple-level MultiIndex**! The original date index is expanded, with `year` and `month` added as additional index levels. This creates unnecessary complexity for downstream operations.

#### With `group_keys=False` (Current Implementation)

```python
# group_keys=False
report_normal_gp = report_normal_df.groupby(
    [report_normal_df.index.year, report_normal_df.index.month], 
    group_keys=False
)

_m_report_normal = report_normal_gp.get_group((2017, 1))
print(_m_report_normal.index)
```

Output:
```python
DatetimeIndex(['2017-01-04', '2017-01-05', '2017-01-06', ...], 
              dtype='datetime64[ns]', name='date')
```

**Perfect**: The index remains a clean, single-level **DatetimeIndex**!

### 1.5 Why This Matters for the Pipeline

The `group_keys=False` setting is crucial because:

1. **The `_get_risk_analysis_data_with_report()` function** expects a DataFrame with a simple DatetimeIndex
2. **Subsequent calculations** (like extracting year/month for the next steps) become much simpler
3. **Memory efficiency**: Avoiding unnecessary MultiIndex levels reduces complexity
4. **Code readability**: No need to deal with multi-level indexing when accessing data

---

## Part 2: Extracting Group Keys for Iteration

```python
gp_month = sorted(set(report_normal_gp.size().index))
```

This line extracts **all unique (year, month) combinations** from the grouped data and prepares them for chronological iteration.

### 2.1 Step-by-Step Breakdown

#### Step 1: `report_normal_gp.size()`

```python
monthly_counts = report_normal_gp.size()
print(monthly_counts)
```

**Output**:
```
year  month
2017  1        20  # January 2017 has 20 trading days
      2        19  # February 2017 has 19 trading days
      3        23  # March 2017 has 23 trading days
      4        21
      5        22
      6        20
      7        21
      8        22
      9        20
      10       23
      11       21
      12       20
2018  1        22  # January 2018 has 22 trading days
      2        18
      3        22
      4        21
      ...
dtype: int64
```

**What `.size()` does**:
- Returns a **Series** with:
  - **Index**: The group keys (MultiIndex of year and month)
  - **Values**: Number of rows (trading days) in each group
- This is an **aggregation** operation that actually computes something (unlike the groupby object itself, which is lazy)

#### Step 2: `.index` - Extract the Group Keys

```python
group_keys = report_normal_gp.size().index
print(group_keys)
```

**Output**:
```
MultiIndex([(2017, 1), (2017, 2), (2017, 3), (2017, 4), (2017, 5), (2017, 6),
            (2017, 7), (2017, 8), (2017, 9), (2017, 10), (2017, 11), (2017, 12),
            (2018, 1), (2018, 2), (2018, 3), (2018, 4), ...],
           names=['year', 'month'])
```

Now we have **all unique (year, month) combinations** that exist in the data.

#### Step 3: `set()` - Ensure Uniqueness (Optional Safety)

```python
unique_keys = set(report_normal_gp.size().index)
```

**Why use `set()`?**
- The index from `.size()` is already unique (each group appears once)
- But using `set()` is a **defensive programming** practice:
  - Guarantees uniqueness even if something unexpected happens
  - Makes the code more robust
  - No downside (minimal performance cost)

#### Step 4: `sorted()` - Ensure Chronological Order

```python
gp_month = sorted(set(report_normal_gp.size().index))
print(gp_month)
```

**Output**:
```
[(2017, 1), (2017, 2), (2017, 3), (2017, 4), (2017, 5), (2017, 6),
 (2017, 7), (2017, 8), (2017, 9), (2017, 10), (2017, 11), (2017, 12),
 (2018, 1), (2018, 2), (2018, 3), (2018, 4), ...]
```

**Why sorting is critical**:
- Sets are **unordered** in Python
- Without sorting, months would be processed in random order
- For time series analysis, **chronological order is essential**:
  - Charts should show time progression
  - Calculations that depend on order (like cumulative metrics) would break
- Tuples sort naturally: first by year, then by month

### 2.2 Visualizing the Transformation

```
Original GroupBy Object
    │
    ▼
┌─────────────────────────────────────┐
│ (2017,1): 20 days                   │
│ (2017,2): 19 days                   │
│ (2017,3): 23 days                   │
│ (2018,1): 22 days                   │
│ (2017,12): 20 days                  │
│ (2018,2): 18 days                   │
│ ... (in no particular order)        │
└─────────────────────────────────────┘
    │
    │ .size().index
    ▼
┌─────────────────────────────────────┐
│ MultiIndex([                        │
│    (2017, 1), (2017, 2), (2017, 3), │
│    (2017, 12), (2018, 1), (2018, 2),│
│    ... (still in creation order)    │
│ ])                                  │
└─────────────────────────────────────┘
    │
    │ set() + sorted()
    ▼
┌─────────────────────────────────────┐
│ [(2017, 1), (2017, 2), (2017, 3),  │
│  (2017, 4), (2017, 5), (2017, 6),  │
│  (2017, 7), (2017, 8), (2017, 9),  │
│  (2017, 10), (2017, 11), (2017, 12),│
│  (2018, 1), (2018, 2), (2018, 3),  │
│  ...]                               │
└─────────────────────────────────────┘
    │
    │ Used in for loop
    ▼
    for gp_m in gp_month:
        # Process months in order
```

---

## Part 3: Calculating Month-End Dates

```python
month_days = pd.Timestamp(year=gp_m[0], month=gp_m[1], day=1).days_in_month
```

### 3.1 Step-by-Step Breakdown

#### Step 1: `gp_m[0]` and `gp_m[1]`
- `gp_m` is a tuple `(year, month)`
- `gp_m[0]` = year (e.g., 2017)
- `gp_m[1]` = month (e.g., 1 for January)

#### Step 2: `pd.Timestamp(year=..., month=..., day=1)`
Creates a timestamp pointing to the **first day** of that month:

```python
# If gp_m = (2017, 1)
pd.Timestamp(year=2017, month=1, day=1)
# Output: Timestamp('2017-01-01 00:00:00')
```

#### Step 3: `.days_in_month`
This is a Pandas Timestamp property that returns the number of days in that month:

```python
# For January 1, 2017
pd.Timestamp(2017, 1, 1).days_in_month
# Output: 31

# For February 1, 2017  
pd.Timestamp(2017, 2, 1).days_in_month
# Output: 28 (non-leap year)

# For February 1, 2020 (leap year)
pd.Timestamp(2020, 2, 1).days_in_month  
# Output: 29
```

### 3.2 Why This Approach?

This line calculates the **total days in the month** to construct the month's last day:

```python
# Full usage in the code:
month_days = pd.Timestamp(year=gp_m[0], month=gp_m[1], day=1).days_in_month
month_end_date = pd.Timestamp(year=gp_m[0], month=gp_m[1], day=month_days)

# If gp_m = (2017, 1):
# month_days = 31
# month_end_date = Timestamp('2017-01-31')
```

Different months have different lengths, and leap years add complexity:
| Month | Days | Special Case |
|-------|------|--------------|
| January | 31 | Fixed |
| February | 28 or 29 | 29 in leap years |
| March | 31 | Fixed |
| April | 30 | Fixed |
| ... | ... | ... |

Using `.days_in_month` **automatically handles all cases** without manual leap year checking.

---

## Part 4: Aggregating Monthly Results

```python
_temp_df = _get_risk_analysis_data_with_report(
    _m_report_normal, 
    month_end_date
)
_monthly_df = pd.concat([_monthly_df, _temp_df], sort=False)
```

### 4.1 Part 1: Calling `_get_risk_analysis_data_with_report()`

This function (explained in previous analyses) calculates risk metrics for one month of data:

```python
def _get_risk_analysis_data_with_report(
    report_normal_df: pd.DataFrame,  # All trading days in current month
    date: pd.Timestamp,               # Last day of that month
) -> pd.DataFrame:
    # Calculate excess return series and call risk_analysis()
    # Returns a MultiIndex DataFrame with a date column
```

**Input Example (January 2017)**:
- `_m_report_normal`: Contains all 20 trading days in January with `return`, `cost`, `bench`, `turnover`
- `date`: `Timestamp('2017-01-31')` (last day of the month)

**Output Example (`_temp_df`)**:

```
                                             risk        date
excess_return_without_cost mean               0.002345   2017-01-31
                           std                0.004567   2017-01-31
                           annualized_return  0.156789   2017-01-31
                           information_ratio  1.876543   2017-01-31
                           max_drawdown      -0.065432   2017-01-31
excess_return_with_cost    mean               0.001234   2017-01-31
                           std                0.004566   2017-01-31
                           annualized_return  0.125678   2017-01-31
                           information_ratio  1.543210   2017-01-31
                           max_drawdown      -0.076543   2017-01-31
```

### 4.2 Part 2: `pd.concat([_monthly_df, _temp_df], sort=False)`

This line appends the newly calculated monthly data to the accumulating dataset:

```python
_monthly_df = pd.concat([_monthly_df, _temp_df], sort=False)
```

#### Step-by-Step Demonstration:

**First Loop (January 2017)**:
```python
_monthly_df = pd.DataFrame()  # Initially empty
_temp_df = <January 2017 data>

# After concat:
_monthly_df = 
                                             risk        date
excess_return_without_cost mean               0.002345   2017-01-31
                           std                0.004567   2017-01-31
                           ...                ...        ...
excess_return_with_cost    mean               0.001234   2017-01-31
                           ...                ...        ...
```

**Second Loop (February 2017)**:
```python
_temp_df = <February 2017 data>

# After concat:
_monthly_df = 
                                             risk        date
excess_return_without_cost mean               0.002345   2017-01-31  ← January data
                           std                0.004567   2017-01-31
                           ...                ...        ...
excess_return_with_cost    mean               0.001234   2017-01-31
                           ...                ...        ...
excess_return_without_cost mean               0.003456   2017-02-28  ← February data (appended)
                           std                0.005678   2017-02-28
                           ...                ...        ...
excess_return_with_cost    mean               0.002345   2017-02-28
                           ...                ...        ...
```

**Third Loop (March 2017)**: Continue appending...

### 4.3 The Role of `sort=False`

The `sort=False` parameter controls whether the columns are sorted alphabetically during concatenation.

#### With `sort=True` (Default Behavior):
```python
# If columns from different DataFrames are in different orders
df1 = pd.DataFrame({'B': [1], 'A': [2]})  # Columns: B, A
df2 = pd.DataFrame({'A': [3], 'B': [4]})  # Columns: A, B

result = pd.concat([df1, df2], sort=True)
# Columns are sorted alphabetically: A, B
# Result:
#    A  B
# 0  2  1
# 0  3  4
```

#### With `sort=False` (Current Implementation):
```python
result = pd.concat([df1, df2], sort=False)
# Columns maintain the order from the first DataFrame
# Result:
#    B  A
# 0  1  2
# 0  4  3
```

**Why `sort=False` is used here:**

1. **Column Order Consistency**: All `_temp_df` DataFrames from `_get_risk_analysis_data_with_report()` have identical column structures (always `'risk'` and `'date'` columns in that order)
2. **Performance**: Skipping unnecessary sorting saves computational time, especially when concatenating many months
3. **Predictable Output**: The resulting `_monthly_df` maintains the same column order throughout

### 4.4 The Final `_monthly_df`

After processing all months, `_monthly_df` contains:
- **Rows**: All risk metrics for all months stacked vertically
- **Columns**: `'risk'` (metric values) and `'date'` (month-end timestamps)
- **Index**: MultiIndex with:
  - Level 0: Metric category (`excess_return_without_cost`, `excess_return_with_cost`)
  - Level 1: Risk indicator (`mean`, `std`, `annualized_return`, etc.)

This structure is perfectly prepared for the next step: extracting time series for each risk indicator with `_get_monthly_analysis_with_feature()`.

---

## Summary: The Complete Pipeline

```
report_normal_df (daily data)
    │
    ▼
GroupBy [(year, month)] with group_keys=False
    │
    ├──► report_normal_gp (GroupBy object)
    │       │
    │       │ .size().index
    │       ▼
    │   MultiIndex of all (year, month) combinations
    │       │
    │       │ set() + sorted()
    │       ▼
    │   gp_month = [(2017,1), (2017,2), ...] (chronological order)
    │
    ▼
for gp_m in gp_month:
    │
    ├──► monthly_data = report_normal_gp.get_group(gp_m)  # Clean DatetimeIndex
    ├──► if len(monthly_data) >= 3:
    │       │
    │       │ # Calculate month-end date
    │       ├──► month_days = pd.Timestamp(gp_m[0], gp_m[1], 1).days_in_month
    │       ├──► month_end = pd.Timestamp(gp_m[0], gp_m[1], month_days)
    │       │
    │       │ # Calculate monthly risk metrics
    │       ├──► _temp_df = _get_risk_analysis_data_with_report(monthly_data, month_end)
    │       │
    │       │ # Append to accumulating DataFrame
    │       └──► _monthly_df = pd.concat([_monthly_df, _temp_df], sort=False)
    │
    └──► Continue to next month

    │
    ▼
_monthly_df (all months stacked)
    │
    ▼
_get_monthly_analysis_with_feature() for each risk indicator
    │
    ▼
Monthly time series plots
```

# _get_risk_analysis_figure function process

**Source Code Reference**: [https://github.com/microsoft/qlib/blob/main/qlib/contrib/report/analysis_position/risk_analysis.py#L91](https://github.com/microsoft/qlib/blob/main/qlib/contrib/report/analysis_position/risk_analysis.py#L91)

You've noticed something important! The `'risk'` column name **disappears** during this transformation. Let me explain why this happens and why it's the right design choice.

---

## Step 1: Tracing the 'risk' Column Through the Pipeline

### In `_get_risk_analysis_data_with_report()` - The Origin

```python
def _get_risk_analysis_data_with_report(...):
    analysis = dict()
    analysis["excess_return_without_cost"] = risk_analysis(...)  # Returns DataFrame with 'risk' column
    analysis["excess_return_with_cost"] = risk_analysis(...)     # Returns DataFrame with 'risk' column
    
    analysis_df = pd.concat(analysis)  # MultiIndex rows, single 'risk' column
    analysis_df["date"] = date
    return analysis_df

# risk_analysis() returns:
#                         risk
# mean                 0.000692
# std                  0.005374
# annualized_return    0.174495
# information_ratio    2.045576
# max_drawdown        -0.079103
```

### In `_monthly_df` - The 'risk' Column Persists

```python
# _monthly_df from _get_monthly_risk_analysis_with_report()
                                             risk        date
excess_return_without_cost mean               0.002345   2017-01-31
                           std                0.004567   2017-01-31
                           annualized_return  0.156789   2017-01-31
                           ...                ...        ...
excess_return_with_cost    mean               0.001234   2017-01-31
                           ...                ...        ...
```

### In `_name_df` - Still There

```python
# After _monthly_df_gp.get_group(feature).set_index(["level_0", "level_1"])
_name_df = ...

                                            risk       date
level_0                    level_1          
excess_return_without_cost annualized_return 0.156789  2017-01-31
excess_return_with_cost    annualized_return 0.125678  2017-01-31
...                                           ...       ...
```

---

## Step 2: What Happens During `pivot_table`

### Before Pivot - Structure
```
DataFrame: _name_df
├── Index: MultiIndex (level_0, level_1)
└── Columns:
    ├── 'risk' (the actual values)
    └── 'date' (row identifier for pivot)
```

### During Pivot - The 'risk' Column is Consumed

```python
_temp_df = _name_df.pivot_table(
    index="date",           # 'date' becomes the new row index
    values=["risk"],        # 'risk' provides the cell values
    columns=_name_df.index   # Index becomes column headers
)
```

The `values=["risk"]` parameter **consumes** the 'risk' column. Its contents are distributed into the cells of the new DataFrame, and the column name `'risk'` is **promoted** to become the **top level of the column MultiIndex**.

### After Pivot - 'risk' Becomes Level 0 of Column MultiIndex

```python
print(_temp_df.columns)

MultiIndex([('risk', ('excess_return_without_cost', 'annualized_return')),
            ('risk', ('excess_return_with_cost', 'annualized_return'))],
           names=[None, None])
```

**What happened:**
- The column name `'risk'` is now the **first level** of the MultiIndex
- The original index tuples become the **second level**
- The actual values that were in the 'risk' column are now in the DataFrame cells

### Visual Representation

```
BEFORE PIVOT:
┌─────────────────────────────────────────────────────────────┐
│ _name_df                                                    │
├───────────────────┬───────────────────┬─────────┬──────────┤
│ Index (level_0)   │ Index (level_1)   │ risk    │ date     │ ← 'risk' is a column
├───────────────────┼───────────────────┼─────────┼──────────┤
│ without_cost      │ annualized        │ 0.156789│ 2017-01-31│
│ with_cost         │ annualized        │ 0.125678│ 2017-01-31│
│ without_cost      │ annualized        │ 0.167890│ 2017-02-28│
│ with_cost         │ annualized        │ 0.134567│ 2017-02-28│
└───────────────────┴───────────────────┴─────────┴──────────┘
                           │
                           │ pivot_table(values=["risk"])
                           ▼

AFTER PIVOT:
┌─────────────────────────────────────────────────────────────┐
│ _temp_df                                                     │
├───────────────┬─────────────────────────────────────────────┤
│               │ risk                                         │ ← 'risk' becomes top level
│               ├─────────────────────┬───────────────────────┤
│ date          │ (without_cost, annualized) │ (with_cost, annualized) │
├───────────────┼─────────────────────┼───────────────────────┤
│ 2017-01-31    │ 0.156789            │ 0.125678              │ ← values now in cells
│ 2017-02-28    │ 0.167890            │ 0.134567              │
└───────────────┴─────────────────────┴───────────────────────┘
```

---

## Step 3: The Lambda Function - Why 'risk' Disappears

### Understanding `x[-1]` in Context

```python
# Each column x is a tuple: ('risk', ('excess_return_without_cost', 'annualized_return'))
# x[0] = 'risk'
# x[-1] = ('excess_return_without_cost', 'annualized_return')

new_names = map(lambda x: "_".join(x[-1]), _temp_df.columns)
```

**The lambda function deliberately IGNORES `x[0]` (the 'risk' part)!**

### Why This Makes Sense

1. **'risk' is redundant information** - All columns contain risk values, so having 'risk' in every column name adds no value
2. **The meaningful identifiers** are the strategy category and metric name
3. **Column names become cleaner** - `'excess_return_without_cost_annualized_return'` vs `'risk_excess_return_without_cost_annualized_return'`

### Comparison

```python
# What would happen if we kept 'risk':
# (Hypothetical) lambda x: "_".join(x)  # Join both levels
new_names_bad = ['risk_excess_return_without_cost_annualized_return', 
                 'risk_excess_return_with_cost_annualized_return']

# What actually happens (current code):
new_names_good = ['excess_return_without_cost_annualized_return', 
                  'excess_return_with_cost_annualized_return']
```

---

## Step 4: Visualizing the Complete Transformation

```
Phase 1: Original Data (with 'risk' column)
┌─────────────────────────────────────────────────────┐
│         level_0     level_1    risk        date     │
│ 0  without_cost  annualized  0.156789  2017-01-31   │
│ 1  with_cost     annualized  0.125678  2017-01-31   │
│ 2  without_cost  annualized  0.167890  2017-02-28   │
│ 3  with_cost     annualized  0.134567  2017-02-28   │
└─────────────────────────────────────────────────────┘
                           │
                           │ pivot_table(index="date", values=["risk"], columns=index)
                           ▼

Phase 2: After Pivot (MultiIndex columns with 'risk')
┌─────────────────────────────────────────────────────┐
│ date        risk                                    │
│             (without_cost, annualized)  (with_cost, annualized) │
├────────────┼──────────────────────────┼──────────────────────────┤
│ 2017-01-31 │ 0.156789                 │ 0.125678                 │
│ 2017-02-28 │ 0.167890                 │ 0.134567                 │
└────────────┴──────────────────────────┴──────────────────────────┘
                           │
                           │ map(lambda x: "_".join(x[-1]))
                           ▼

Phase 3: Final Result ('risk' removed)
┌─────────────────────────────────────────────────────┐
│ date        without_cost_annualized  with_cost_annualized │
├────────────┼────────────────────────┼──────────────────────┤
│ 2017-01-31 │ 0.156789               │ 0.125678             │
│ 2017-02-28 │ 0.167890               │ 0.134567             │
└────────────┴────────────────────────┴──────────────────────┘
```

---

## Step 5: Why This is the Right Design Choice

### 1. **No Information Loss**

The fact that these are "risk" values is preserved in:
- The **context** of the function (it's called `_get_monthly_analysis_with_feature`)
- The **variable names** (`_temp_df` contains risk metrics)
- The **column names** (they include the specific metric like `annualized_return`)

### 2. **Cleaner Column Names**

```python
# With 'risk' (verbose and redundant)
column_with_risk = 'risk_excess_return_without_cost_annualized_return'

# Without 'risk' (clean and readable)
column_clean = 'excess_return_without_cost_annualized_return'
```
