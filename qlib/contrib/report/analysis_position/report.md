# Understanding Qlib's Report Data Preprocessing: Adding a Starting Point "T0"

**Source Code Reference**: [https://github.com/microsoft/qlib/blob/main/qlib/contrib/report/analysis_position/report.py#L80](https://github.com/microsoft/qlib/blob/main/qlib/contrib/report/analysis_position/report.py#L80)

This document explains a specific code snippet in Qlib that adds a virtual starting point "T0" to backtest report data for better visualization of cumulative return curves.

## 1. Original Data Example

Assume `_calculate_report_data()` produces the following `report_df`:

| date       | cum_return_wo_cost | turnover |
|------------|-------------------|----------|
| 2024-01-01 | 0.01              | 0.20     |
| 2024-01-02 | 0.03              | 0.15     |
| 2024-01-03 | 0.02              | 0.10     |

Index name = "date"

## 2. Step 1: Reset Index
```python
_temp_df = report_df.reset_index()
```
Convert index into a regular column.

Result:

| index | date       | cum_return_wo_cost | turnover |
|-------|------------|-------------------|----------|
| 0     | 2024-01-01 | 0.01              | 0.20     |
| 1     | 2024-01-02 | 0.03              | 0.15     |
| 2     | 2024-01-03 | 0.02              | 0.10     |

## 3. Step 2: Add a Zero Row
```python
_temp_df.loc[-1] = 0
```
Add a row with all zeros (index = -1).

Result:

| index | date       | cum_return_wo_cost | turnover |
|-------|------------|-------------------|----------|
| -1    | 0          | 0                 | 0        |
| 0     | 2024-01-01 | 0.01              | 0.20     |
| 1     | 2024-01-02 | 0.03              | 0.15     |
| 2     | 2024-01-03 | 0.02              | 0.10     |

## 4. Step 3: Shift Down
```python
_temp_df = _temp_df.shift(1)
```
Shift all data down by 1 row.

Result:

| index | date       | cum_return_wo_cost | turnover |
|-------|------------|-------------------|----------|
| -1    | NaN        | NaN               | NaN      |
| 0     | 0          | 0                 | 0        |
| 1     | 2024-01-01 | 0.01              | 0.20     |
| 2     | 2024-01-02 | 0.03              | 0.15     |
| 3     | 2024-01-03 | 0.02              | 0.10     |

## 5. Step 4: Set First Row Date to "T0"
```python
_temp_df.loc[0, index_name] = "T0"  # index_name = "date"
```
Set the date of the first row to "T0".

Result:

| index | date       | cum_return_wo_cost | turnover |
|-------|------------|-------------------|----------|
| -1    | NaN        | NaN               | NaN      |
| 0     | T0         | 0                 | 0        |
| 1     | 2024-01-01 | 0.01              | 0.20     |
| 2     | 2024-01-02 | 0.03              | 0.15     |
| 3     | 2024-01-03 | 0.02              | 0.10     |

## 6. Step 5: Restore Date as Index
```python
_temp_df.set_index(index_name, inplace=True)
```
Set "date" column back as the index.

Result:

| date       | cum_return_wo_cost | turnover |
|------------|-------------------|----------|
| NaN        | NaN               | NaN      |
| T0         | 0                 | 0        |
| 2024-01-01 | 0.01              | 0.20     |
| 2024-01-02 | 0.03              | 0.15     |
| 2024-01-03 | 0.02              | 0.10     |

## 7. Step 6: Critical Cleanup
```python
_temp_df.iloc[0] = 0
```
Set all values in the first row to 0.

Before (first row):
| date | cum_return_wo_cost | turnover |
|------|-------------------|----------|
| NaN  | NaN               | NaN      |

After:
| date | cum_return_wo_cost | turnover |
|------|-------------------|----------|
| NaN  | 0                 | 0        |

## 8. Final Result

| date       | cum_return_wo_cost | turnover |
|------------|-------------------|----------|
| NaN        | 0                 | 0        |
| T0         | 0                 | 0        |
| 2024-01-01 | 0.01              | 0.20     |
| 2024-01-02 | 0.03              | 0.15     |
| 2024-01-03 | 0.02              | 0.10     |

## 9. Why This Matters (Core Logic)

The purpose of this code is to **add a starting point "T0" to the backtest chart**.

Without this modification, the cumulative return curve would start from the first actual data point:

```
2024-01-01 -> 0.01
```

This would make the curve start at 0.01 instead of 0, which is visually incorrect.

By adding "T0" with value 0, the chart becomes:

```
T0          0
2024-01-01  0.01
2024-01-02  0.03
```

This provides a more reasonable and visually appealing curve that starts from zero.

## 10. Why `_temp_df.iloc[0] = 0` Is Necessary

The `shift(1)` operation creates a row with NaN values at the top. This line ensures that:

- The chart doesn't encounter errors from NaN values
- All plotting libraries can properly render the curve
- The starting point is guaranteed to be exactly 0 (eliminating any floating-point errors)
