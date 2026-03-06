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

## Execution Flow of `group_scatter_figure` in `_group_return`

**Source file**: [qlib/contrib/report/analysis_model/analysis_model_performance.py#L57](https://github.com/microsoft/qlib/blob/main/qlib/contrib/report/analysis_model/analysis_model_performance.py#L57)

This line of code creates the cumulative return chart for the grouped portfolios. While it appears simple, it triggers a complex chain of internal calls within the `ScatterGraph` class.

### Overall Process Overview

```
1. Create ScatterGraph instance
   ↓
2. ScatterGraph.__init__() initialization
   ↓
3. Call _init_data() → _get_data() to generate traces
   ↓
4. Access .figure property to obtain final Figure
   ↓
5. Return Plotly Figure object
```

---

### Detailed Execution Flow

#### Step 1: Create `ScatterGraph` Instance

```python
group_scatter_figure = ScatterGraph(
    t_df.cumsum(),  # Data: cumulative returns DataFrame
    layout=dict(    # Layout settings
        title="Cumulative Return",
        xaxis=dict(
            tickangle=45, 
            rangebreaks=kwargs.get("rangebreaks", guess_plotly_rangebreaks(t_df.index))
        ),
    ),
).figure
```

**What happens here**:
- `t_df.cumsum()` is a DataFrame containing cumulative returns for all groups (Group1~Group5, long-short, long-average)
- The `layout` dictionary defines the chart title and X-axis styling
- The `rangebreaks` parameter hides non-trading days (like weekends), either user-provided or auto-detected by `guess_plotly_rangebreaks()`

#### Step 2: Call `ScatterGraph.__init__`

`ScatterGraph` inherits from `BaseGraph`, so it calls the parent's `__init__`:

```python
class ScatterGraph(BaseGraph):
    _name = "scatter"  # Set chart type name
    # No own __init__, uses parent's directly
```

Entering `BaseGraph.__init__`:

```python
def __init__(self, df, layout=None, graph_kwargs=None, name_dict=None, **kwargs):
    self._df = df                    # Store data
    self._layout = layout or {}       # Store layout
    self._graph_kwargs = graph_kwargs or {}
    
    # If no name_dict provided, auto-create {column_name: column_name}
    if name_dict is None:
        self._name_dict = {col: col for col in df.columns}
    
    self._init_parameters(**kwargs)  # Initialize parameters
    self._init_data()                 # ★ Core: generate data
```

#### Step 3: `_init_parameters()` Sets Chart Type

```python
def _init_parameters(self, **kwargs):
    # self._name comes from ScatterGraph's "scatter"
    self._graph_type = self._name.lower().capitalize()  # "scatter" → "Scatter"
```

#### Step 4: `_init_data()` Calls `_get_data()` to Generate Traces

```python
def _init_data(self):
    if self._df.empty:
        raise ValueError("df is empty.")
    self.data = self._get_data()  # ← Generate all traces
```

`_get_data()` method (parent class default implementation):

```python
def _get_data(self) -> list:
    _data = [
        self.get_instance_with_graph_parameters(
            graph_type=self._graph_type,  # "Scatter"
            x=self._df.index,              # X-axis: dates
            y=self._df[_col],              # Y-axis: current column's data
            name=_name,                     # Legend name
            **self._graph_kwargs             # Other parameters (e.g., mode="lines+markers")
        )
        for _col, _name in self._name_dict.items()  # Iterate over each column
    ]
    return _data
```

**Data Example**:
Assuming `t_df.cumsum()` has 7 columns (Group1~Group5 + long-short + long-average):

```python
self._name_dict = {
    "Group1": "Group1",
    "Group2": "Group2",
    "Group3": "Group3",
    "Group4": "Group4",
    "Group5": "Group5",
    "long-short": "long-short",
    "long-average": "long-average"
}

# _get_data() returns _data containing 7 traces
_data = [
    go.Scatter(name='Group1', x=dates, y=group1_values, ...),
    go.Scatter(name='Group2', x=dates, y=group2_values, ...),
    ...
    go.Scatter(name='long-average', x=dates, y=long_avg_values, ...)
]
```

#### Step 5: `.figure` Property Generates Final Figure

```python
@property
def figure(self) -> go.Figure:
    _figure = go.Figure(
        data=self.data,              # Trace list from previous step
        layout=self._get_layout()     # Get layout
    )
    # Use Plotly 3.x default theme
    _figure["layout"].update(template=None)
    return _figure
```

`_get_layout()` method:

```python
def _get_layout(self) -> go.Layout:
    return go.Layout(**self._layout)  # Unpack dict as layout parameters
```

**Layout Example**:
```python
self._layout = {
    "title": "Cumulative Return",
    "xaxis": {
        "tickangle": 45,
        "rangebreaks": [{"values": ["2026-03-07"], "dvalue": 172800000}]
    }
}

# Converted to
layout = go.Layout(
    title="Cumulative Return",
    xaxis=dict(tickangle=45, rangebreaks=[...])
)
```

---

### Complete Call Chain Diagram

```
ScatterGraph(t_df.cumsum(), layout=...)
    │
    ↓ [Instantiation]
ScatterGraph.__init__ (inherits from BaseGraph)
    ├─ self._df = t_df.cumsum()
    ├─ self._layout = {...}
    ├─ self._name_dict = {col:col for col in df.columns} (7 columns → 7 key-value pairs)
    ├─ self._init_parameters()
    │     └─ self._graph_type = "Scatter"
    └─ self._init_data()
          └─ self.data = self._get_data()
                │
                ↓ [List comprehension, 7 iterations]
                for _col, _name in self._name_dict.items():
                    go.Scatter(
                        x=df.index,
                        y=df[_col],
                        name=_name,
                        mode=None,  # from self._graph_kwargs
                        ...
                    )
                │
                ↓
                self.data = [trace1, trace2, ..., trace7]
    │
    ↓ [Access .figure property]
    .figure
    ├─ go.Figure(data=self.data, layout=self._get_layout())
    ├─ _figure.layout.update(template=None)
    └─ return _figure

