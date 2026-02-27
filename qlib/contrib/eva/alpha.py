## `label.index.get_level_values(1).unique()` Explanation

**Source file**: [qlib/contrib/eva/alpha.py](https://github.com/microsoft/qlib/blob/main/qlib/contrib/eva/alpha.py#L14)

This line of code is used to **obtain a list of all unique stock codes**.

### Code Breakdown

```python
label.index                # Get the index of label (MultiIndex)
    .get_level_values(1)   # Get the 1st level (instrument/stock code)
    .unique()              # Remove duplicates, get unique stock codes
    len()                  # Count the number of stocks
```

### MultiIndex Structure

```python
# label's index is a MultiIndex with two levels:
# Level 0: datetime
# Level 1: instrument (stock code)

label.index
# MultiIndex([('2026-02-17', 'SH600000'),
#             ('2026-02-17', 'SH600001'),
#             ('2026-02-17', 'SH600002'),
#             ('2026-02-18', 'SH600000'),
#             ('2026-02-18', 'SH600001'),
#             ('2026-02-18', 'SH600003'),
#             ('2026-02-19', 'SH600001'),
#             ('2026-02-19', 'SH600002'),
#             ('2026-02-19', 'SH600004')],
#            names=['datetime', 'instrument'])
```

### Step-by-Step Extraction

```python
# 1. label.index → Get the entire MultiIndex
idx = label.index

# 2. .get_level_values(1) → Get level 1 (stock codes)
instruments = idx.get_level_values(1)
# Result:
# ['SH600000', 'SH600001', 'SH600002', 
#  'SH600000', 'SH600001', 'SH600003',
#  'SH600001', 'SH600002', 'SH600004']

# 3. .unique() → Remove duplicates
unique_instruments = instruments.unique()
# Result: ['SH600000', 'SH600001', 'SH600002', 'SH600003', 'SH600004']

# 4. len() → Count the number of stocks
stock_count = len(unique_instruments)  # 5
```

## Three Lines of Code Explanation

These three lines are used to **calculate the daily precision rate for long positions**.

### Line-by-Line Explanation

#### Line 1: Group by Date

```python
groupll = long.groupby(date_col, group_keys=False)
```

`long` contains the selected long stocks and their actual returns for each day. This line regroups by date to prepare for calculating daily long precision.

#### Line 2: Check if Returns are Positive

```python
l_dom = groupll.apply(lambda x: x > 0)
```

For each day's long stocks, check if their returns are greater than 0 (whether they went up). Returns a Series of True/False.

#### Line 3: Count

```python
l_c = groupll.count()
```

Count how many long stocks there are each day.

### Complete Example

Assume data for two days:

```python
import pandas as pd

# long contains selected long stocks and their returns
# Format: MultiIndex (datetime, instrument), values are returns
long = pd.Series(
    [0.05, 0.04, -0.02, 0.03, 0.01, -0.01],
    index=pd.MultiIndex.from_tuples([
        ('2026-02-17', 'SH600000'),
        ('2026-02-17', 'SH600001'),
        ('2026-02-17', 'SH600002'),
        ('2026-02-18', 'SH600000'),
        ('2026-02-18', 'SH600001'),
        ('2026-02-18', 'SH600003'),
    ])
)

print(long)
# 2026-02-17  SH600000    0.05
#             SH600001    0.04
#             SH600002   -0.02
# 2026-02-18  SH600000    0.03
#             SH600001    0.01
#             SH600003   -0.01
```

#### Step 1: Group by Date

```python
groupll = long.groupby(level='datetime', group_keys=False)
# Divides into two groups:
# Group 1 (2026-02-17): [0.05, 0.04, -0.02]
# Group 2 (2026-02-18): [0.03, 0.01, -0.01]
```

#### Step 2: Check for Positive Returns

```python
l_dom = groupll.apply(lambda x: x > 0)
# Apply x > 0 to each group
# 2026-02-17: [True, True, False]
# 2026-02-18: [True, True, False]

print(l_dom)
# 2026-02-17  SH600000     True
#             SH600001     True
#             SH600002    False
# 2026-02-18  SH600000     True
#             SH600001     True
#             SH600003    False
```

#### Step 3: Count

```python
l_c = groupll.count()
# Count stocks in each group
# 2026-02-17: 3
# 2026-02-18: 3

print(l_c)
# 2026-02-17    3
# 2026-02-18    3
```

### Final Precision Calculation

```python
# Number of positive returns = sum of Trues in l_dom (True=1, False=0)
# Daily positive count = l_dom.groupby(level='datetime').sum()
# Precision = positive count / total count

long_prec = l_dom.groupby(level='datetime').sum() / l_c
# 2026-02-17: 2/3 = 0.667
# 2026-02-18: 2/3 = 0.667
```

### Summary

| Code | Purpose | Result |
|------|---------|--------|
| `groupll = long.groupby(date_col)` | Group by date | Daily long stocks |
| `l_dom = groupll.apply(lambda x: x > 0)` | Check if returns are positive | True/False |
| `l_c = groupll.count()` | Count | Number of stocks per day |
