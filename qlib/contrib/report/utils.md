## `guess_plotly_rangebreaks` Function Explanation

**Source file**: [qlib/contrib/report/utils.py#L49](https://github.com/microsoft/qlib/blob/main/qlib/contrib/report/utils.py#L49)

### Function Purpose

This function automatically detects gaps in a datetime index (such as weekends or holidays) and generates the `rangebreaks` configuration required by Plotly to hide these empty spaces in charts.

### Complete Data Example

Assume we have a datetime index with a weekend gap:

```python
import pandas as pd

dt_index = pd.DatetimeIndex([
    '2026-03-05',  # Thursday
    '2026-03-06',  # Friday
    '2026-03-09',  # Monday (skipping Saturday, Sunday)
    '2026-03-10',  # Tuesday
    '2026-03-11',  # Wednesday
    '2026-03-12'   # Thursday
])
```

---

### Step-by-Step Execution

#### Line 1: Ensure Dates are Sorted

```python
dt_idx = dt_index.sort_values()
```

**Result**:
```python
dt_idx = DatetimeIndex(['2026-03-05', '2026-03-06', '2026-03-09', 
                        '2026-03-10', '2026-03-11', '2026-03-12'])
# Already sorted, unchanged
```

---

#### Line 2: Calculate Gaps Between Consecutive Dates

```python
gaps = dt_idx[1:] - dt_idx[:-1]
```

**Calculation Process**:
```python
dt_idx[1:]  = ['2026-03-06', '2026-03-09', '2026-03-10', '2026-03-11', '2026-03-12']
dt_idx[:-1] = ['2026-03-05', '2026-03-06', '2026-03-09', '2026-03-10', '2026-03-11']

gaps = [
    '2026-03-06' - '2026-03-05' = 1 day,
    '2026-03-09' - '2026-03-06' = 3 days,   # Weekend gap
    '2026-03-10' - '2026-03-09' = 1 day,
    '2026-03-11' - '2026-03-10' = 1 day,
    '2026-03-12' - '2026-03-11' = 1 day
]
```

**Result**:
```python
gaps = [1 day, 3 days, 1 day, 1 day, 1 day]
```

---

#### Line 3: Find the Minimum Gap

```python
min_gap = gaps.min()
```

**Result**:
```python
min_gap = 1 day  # Normal trading day interval
```

---

#### Line 4: Initialize Dictionary

```python
gaps_to_break = {}
```

Prepare a dictionary to store information about gaps that need to be skipped.

---

#### Line 5: Iterate Through Each Gap

```python
for gap, d in zip(gaps, dt_idx[:-1]):
```

**Pairing Relationship**:
```python
zip(gaps, dt_idx[:-1]) generates:
(1 day,  '2026-03-05')  # Pair 1
(3 days, '2026-03-06')  # Pair 2
(1 day,  '2026-03-09')  # Pair 3
(1 day,  '2026-03-10')  # Pair 4
(1 day,  '2026-03-11')  # Pair 5
```

---

#### Lines 6-7: Identify Irregular Gaps

```python
if gap > min_gap:
    gaps_to_break.setdefault(gap - min_gap, []).append(d + min_gap)
```

**Iteration Process**:

| Iteration | gap | d | gap > min_gap? | Operation | Description |
|-----------|-----|---|----------------|-----------|-------------|
| 1 | 1 day | 03-05 | 1 > 1? ❌ | Skip | Normal interval |
| 2 | 3 days | 03-06 | 3 > 1? ✅ | `gap-min_gap=2 days`<br>`d+min_gap=03-07` | Skip 2 days starting from Saturday |
| 3 | 1 day | 03-09 | 1 > 1? ❌ | Skip | Normal interval |
| 4 | 1 day | 03-10 | 1 > 1? ❌ | Skip | Normal interval |
| 5 | 1 day | 03-11 | 1 > 1? ❌ | Skip | Normal interval |

**Detailed Execution for Iteration 2**:
```python
# gap = 3 days, d = '2026-03-06' (Friday)

# Calculate skip duration
skip_duration = gap - min_gap = 3 days - 1 day = 2 days

# Calculate skip start point
start_skip = d + min_gap = '2026-03-06' + 1 day = '2026-03-07' (Saturday)

# Store in dictionary
gaps_to_break.setdefault(2 days, []).append('2026-03-07')
```

**Result**:
```python
gaps_to_break = {
    2 days: ['2026-03-07']  # Skip 2 days starting from Saturday (skip Saturday and Sunday)
}
```

---

#### Line 8: Convert to Plotly Format

```python
return [dict(values=v, dvalue=int(k.total_seconds() * 1000)) for k, v in gaps_to_break.items()]
```

**Conversion Process**:
```python
# k = 2 days
total_seconds = 2 * 24 * 60 * 60 = 172800 seconds
dvalue = 172800 * 1000 = 172800000 milliseconds

# v = ['2026-03-07']
values = ['2026-03-07']
```

**Final Return**:
```python
[
    {
        "values": ["2026-03-07"],  # Start skipping from Saturday
        "dvalue": 172800000         # Skip 172800000 milliseconds (2 days)
    }
]
```

---

### Usage in Plotly

```python
import plotly.graph_objects as go

# Original data
dates = dt_index
values = [10, 12, 15, 14, 16, 18]

fig = go.Figure()
fig.add_trace(go.Scatter(x=dates, y=values, mode='lines+markers'))

# Apply rangebreaks
fig.update_xaxes(rangebreaks=guess_plotly_rangebreaks(dates))
fig.show()
```

**Effect**:
- The x-axis will directly connect Friday to Monday, hiding the Saturday and Sunday gaps
- The chart appears continuous without empty spaces

### Summary Table

| Line | Code | Purpose | Example Result |
|------|------|---------|----------------|
| 1 | `dt_idx.sort_values()` | Ensure dates are ordered | Sorted datetime index |
| 2 | `dt_idx[1:] - dt_idx[:-1]` | Calculate consecutive gaps | `[1,3,1,1,1] days` |
| 3 | `gaps.min()` | Find normal interval | `1 day` |
| 4 | `gaps_to_break = {}` | Initialize storage | `{}` |
| 5 | `for gap, d in zip(...)` | Iterate through pairs | 5 iterations |
| 6-7 | `if gap > min_gap:` | Identify irregular gaps | Skip 2 days from Saturday |
| 8 | `return [dict(...)]` | Convert to Plotly format | `[{"values": ["03-07"], "dvalue": 172800000}]` |
