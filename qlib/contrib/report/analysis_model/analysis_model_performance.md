## Group Return Calculation Logic in `_group_return`

**Source file**: [qlib/contrib/report/analysis_model/analysis_model_performance.py#L38](https://github.com/microsoft/qlib/blob/main/qlib/contrib/report/analysis_model/analysis_model_performance.py#L38)

This code snippet is the core part of the group return calculation. It is used to **sort the data by prediction score each day, evenly divide it into N groups, and calculate the average return for each group**.

### Code Structure

```python
{
    "Group%d" % (i + 1): pred_label_drop.groupby(level="datetime", group_keys=False)["label"].apply(
        lambda x: x[len(x) // N * i : len(x) // N * (i + 1)].mean()
    )
    for i in range(N)
}
```

This is a **dictionary comprehension** that creates one column for each group (Group1 through GroupN).

---

### Step-by-Step Breakdown

#### 1. Outer Loop: Dictionary Comprehension

```python
for i in range(N)  # i = 0, 1, 2, 3, 4 (when N=5)
```

Each iteration creates a group, with keys like `"Group1"`, `"Group2"`, etc.

#### 2. Inner Operation: Group-wise Calculation

```python
pred_label_drop.groupby(level="datetime", group_keys=False)["label"].apply(...)
```

- **Group by date**: One group per day
- **Select the `"label"` column**: Only actual returns are needed
- **`apply`**: Apply the following lambda function to each day's data

#### 3. Lambda Function: Slice and Average

```python
lambda x: x[len(x) // N * i : len(x) // N * (i + 1)].mean()
```

This lambda function is the core. It:
1. **Calculates the group size**: `len(x) // N` (number of stocks per day ÷ number of groups)
2. **Determines the slice range**: from `start` to `end`
3. **Averages the values in that range**

---

### Concrete Calculation Example

Assume:
- `N = 5` (5 groups)
- 10 stocks per day (`len(x) = 10`)
- Group size = `10 // 5 = 2` stocks

| i | Group Name | Slice Range | Indices | Description |
|---|------------|-------------|---------|-------------|
| 0 | Group1 | `0:2` | 1st-2nd | Highest predicted 2 stocks |
| 1 | Group2 | `2:4` | 3rd-4th | Next highest 2 stocks |
| 2 | Group3 | `4:6` | 5th-6th | Middle 2 stocks |
| 3 | Group4 | `6:8` | 7th-8th | Next lowest 2 stocks |
| 4 | Group5 | `8:10` | 9th-10th | Lowest predicted 2 stocks |

---

### Complete Data Example

Assume for a given day, stocks are sorted by prediction score:

```python
# x contains the 'label' values sorted by prediction score
x = [0.05, 0.04, 0.03, 0.02, 0.01, 0.00, -0.01, -0.02, -0.03, -0.04]
len(x) = 10
N = 5
group_size = 10 // 5 = 2
```

**Group Calculations**:

| i | Slice | Selected Values | Average |
|---|-------|-----------------|---------|
| 0 | `0:2` | [0.05, 0.04] | 0.045 |
| 1 | `2:4` | [0.03, 0.02] | 0.025 |
| 2 | `4:6` | [0.01, 0.00] | 0.005 |
| 3 | `6:8` | [-0.01, -0.02] | -0.015 |
| 4 | `8:10` | [-0.03, -0.04] | -0.035 |

---

### Why This Slicing Method?

This slicing approach guarantees:
1. **Evenly sized groups**: Each group contains the same number of stocks (or differs by at most one)
2. **Ordered grouping**: Naturally groups stocks from highest to lowest prediction
3. **No overlap**: Each stock belongs to exactly one group

---

### Final `t_df` Result

Repeating this process for each day yields:

| date | Group1 | Group2 | Group3 | Group4 | Group5 |
|------|--------|--------|--------|--------|--------|
| 2026-03-02 | 0.045 | 0.025 | 0.005 | -0.015 | -0.035 |
| 2026-03-03 | 0.050 | 0.030 | 0.010 | -0.010 | -0.030 |
| 2026-03-04 | 0.040 | 0.020 | 0.000 | -0.020 | -0.040 |

---

## Understanding Long-Short and Long-Average Metrics in `_group_return`

**Source file**: [qlib/contrib/report/analysis_model/analysis_model_performance.py#L50](https://github.com/microsoft/qlib/blob/main/qlib/contrib/report/analysis_model/analysis_model_performance.py#L50)

These two lines of code calculate two key derived metrics from the grouped return data: the **long-short portfolio return** and the **long portfolio excess return over the market average**.

### 1. Long-Short Portfolio Return

```python
t_df["long-short"] = t_df["Group1"] - t_df["Group%d" % N]
```

- **`Group1`**: The average return of the highest predicted group (the long portfolio).
- **`Group%d" % N`**: The average return of the lowest predicted group (the short portfolio). For example, when `N=5`, this becomes `Group5`.
- **`long-short`**: The return of a strategy that goes long on the best group and short on the worst group.

**Mathematical Formula**:
```
long-short = Long Return - Short Return
```

**Why Subtraction?**
- Going long on `Group1` yields a return of `+Group1`.
- Going short on `GroupN` yields a return of `-GroupN` (because shorting profits from a price decrease).
- Total portfolio return = `+Group1 + (-GroupN)` = `Group1 - GroupN`.

**Data Example**:

| date | Group1 | Group5 | long-short |
|------|--------|--------|------------|
| 2026-03-02 | 0.045 | -0.035 | 0.045 - (-0.035) = **0.08** |
| 2026-03-03 | 0.050 | -0.030 | 0.050 - (-0.030) = **0.08** |
| 2026-03-04 | 0.040 | -0.040 | 0.040 - (-0.040) = **0.08** |

---

### 2. Long Portfolio Excess Return (Long-Average)

```python
t_df["long-average"] = t_df["Group1"] - pred_label.groupby(level="datetime", group_keys=False)["label"].mean()
```

- **`Group1`**: The average return of the long portfolio.
- **Market Average**: The equal-weighted average return of all stocks for that day.
- **`long-average`**: The excess return of the long portfolio compared to the overall market average.

**Mathematical Formula**:
```
long-average = Long Return - Market Average Return
```

**Data Example**:

| date | Group1 | Market Average | long-average |
|------|--------|----------------|--------------|
| 2026-03-02 | 0.045 | 0.005 | 0.045 - 0.005 = **0.04** |
| 2026-03-03 | 0.050 | 0.010 | 0.050 - 0.010 = **0.04** |
| 2026-03-04 | 0.040 | 0.000 | 0.040 - 0.000 = **0.04** |

---

### Comparing the Two Metrics

| Metric | Formula | Meaning | Benchmark |
|--------|---------|---------|-----------|
| **long-short** | `Group1 - GroupN` | Absolute return of a market-neutral long-short portfolio | Zero (dollar-neutral) |
| **long-average** | `Group1 - Market Average` | Excess return of the long portfolio | Market average |

### Why Are These Metrics Important?

1. **long-short**: Isolates the model's stock selection ability by removing market-wide effects.
   - A positive value indicates the model can effectively distinguish between good and bad stocks.
   - It is market-neutral and unaffected by general market movements.

2. **long-average**: Measures the model's ability to pick winners.
   - A positive value means the selected stocks outperform the average stock.
   - It is useful for evaluating the potential alpha of a long-only strategy.
