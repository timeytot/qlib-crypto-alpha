# Qlib Report Graph: Automatic Subplot Layout Logic

**Source Code Location**  
[https://github.com/microsoft/qlib/blob/main/qlib/contrib/report/graph.py](https://github.com/microsoft/qlib/blob/main/qlib/contrib/report/graph.py)

The subplot generation in Qlib's reporting module follows a three-step process to create a grid of charts from a DataFrame automatically. Each step is handled by a dedicated method, and all aspects can be customized by the user.

### Process Overview

1. **`_init_subplots_kwargs()`**: Defines the overall grid structure (number of rows/columns, spacing, titles, axis sharing).
2. **`_init_sub_graph_data()`**: Assigns each DataFrame column to a specific cell in the grid (`row`, `col`) and sets the default chart type and style.
3. **`_init_figure()`**: Builds the final Plotly figure by creating the empty grid, generating the individual chart objects, and placing their traces into the correct subplot cells.

### Configuration Parameters and Overrides

The following table summarizes what each method configures and how a user can override the defaults.

| Feature | Controlling Method | What it Sets | User Can Override? |
|---------|--------------------|--------------|---------------------|
| **Grid Size** | `_init_subplots_kwargs()` | `rows`, `cols`, `vertical_spacing` | Yes, by passing a custom `subplots_kwargs` dictionary to the constructor. |
| **Subplot Titles** | `_init_subplots_kwargs()` | `subplot_titles` (defaults to DataFrame column names) | Yes, by providing a custom `subplots_kwargs` with a `subplot_titles` list. |
| **Axis Sharing** | `_init_subplots_kwargs()` | `shared_xaxes=False`, `shared_yaxes=False` | Yes, by setting `shared_xaxes` or `shared_yaxes` to `True` in a custom `subplots_kwargs`. |
| **Subplot Positioning** | `_init_sub_graph_data()` | `row` and `col` for each column | Yes, by providing a custom `sub_graph_data` list that explicitly defines the position for each subplot. |
| **Chart Type & Style** | `_init_sub_graph_data()` | `kind` (e.g., `"ScatterGraph"`) and `graph_kwargs` (default styles) | Yes, by providing a custom `kind_map` dictionary for global defaults, or by defining `kind` and `graph_kwargs` per subplot in a custom `sub_graph_data` list. |

This design provides a powerful default layout while maintaining full flexibility for users who need fine-grained control over their visualizations.

## Understanding `SubplotsGraph` Default Layout Initialization

**Source file**: [qlib/contrib/report/graph.py#L295](https://github.com/microsoft/qlib/blob/main/qlib/contrib/report/graph.py#L295)

The following code snippets are core parts of the `_init_subplots_kwargs()` and `_init_sub_graph_data()` methods. They are used to **calculate and set the default parameters for the subplot grid** when the user does not provide custom layout configurations.

### 1. Calculating the Number of Rows (`_init_subplots_kwargs`). This method defines the **overall grid structure** (how many rows/columns, spacing, titles, etc.).

```python
_rows = math.ceil(len(self._df.columns) / 2)
```

- **`len(self._df.columns)`**: The number of columns in the DataFrame, which equals the number of subplots to display.
- **`/ 2`**: The default setting places **2 subplots per row**.
- **`math.ceil()`**: Rounds up to ensure all subplots fit in the grid.

**Example**:
```python
# Assuming df has 5 columns
len(df.columns) = 5
_rows = math.ceil(5 / 2) = math.ceil(2.5) = 3
# 3 rows are needed to display 5 subplots (2 per row)
```

### 2. Setting Vertical Spacing

```python
self._subplots_kwargs["vertical_spacing"] = 0.3 / _rows
```

- **`vertical_spacing`**: The proportional gap between subplots.
- **`0.3 / _rows`**: More rows result in smaller spacing to maintain overall visual balance.

**Example**:
```python
# With 3 rows
vertical_spacing = 0.3 / 3 = 0.1 (10% spacing)

# With 1 row
vertical_spacing = 0.3 / 1 = 0.3 (30% spacing)
```

### 3. Setting Subplot Titles

```python
self._subplots_kwargs["subplot_titles"] = self._df.columns.tolist()
```

This uses the DataFrame's column names as the titles for each subplot. For example: `["IC", "Rank_IC", "FFR"]`.

### 4. Disabling Axis Sharing

```python
self._subplots_kwargs["shared_xaxes"] = False
self._subplots_kwargs["shared_yaxes"] = False
```

- **`shared_xaxes=False`**: Each subplot maintains its own independent x-axis.
- **`shared_yaxes=False`**: Each subplot maintains its own independent y-axis.

### Complete Default Configuration Example

Assuming a DataFrame with 5 columns:

```python
df = pd.DataFrame({
    "IC": [...],
    "Rank_IC": [...],
    "FFR": [...],
    "PA": [...],
    "POS": [...]
})

# Generated default parameters
self._subplots_kwargs = {
    "rows": 3,                    # 5 columns need 3 rows
    "cols": 2,                     # 2 columns per row
    "shared_xaxes": False,         # Independent X axes
    "shared_yaxes": False,         # Independent Y axes
    "vertical_spacing": 0.1,       # 10% vertical spacing
    "print_grid": False,           # Do not print grid info
    "subplot_titles": ["IC", "Rank_IC", "FFR", "PA", "POS"]  # Subplot titles
}
```

### Final Layout Visualization

```
Row 1, Col 1     Row 1, Col 2
[IC Subplot]     [Rank_IC Subplot]
  Title: IC        Title: Rank_IC

Row 2, Col 1     Row 2, Col 2
[FFR Subplot]    [PA Subplot]
  Title: FFR       Title: PA

Row 3, Col 1     Row 3, Col 2
[POS Subplot]    [Empty]
  Title: POS

Vertical spacing = 10% of subplot height
```

---

## Understanding `_init_sub_graph_data()`
This method runs only when sub_graph_data is None (no user-defined layout).It creates a list that tells Plotly:
“Column X should go to row Y, column Z, with title W, using graph type V.”
This method **automatically generates configuration data for each subplot** when the user does not provide `sub_graph_data`. It assigns a position (row and column) in the grid to each column of the DataFrame.

### Key Variables

```python
self.__cols = self._subplots_kwargs.get("cols", 2)  # Number of columns in the grid (default 2)
```

- **`self.__cols`**: The total number of columns in the subplot grid. It defaults to `2` if not specified in `subplots_kwargs`. This value determines the grid's column count and is used to calculate each subplot's position.

### The Method Code

### The Column Calculation Logic

```python
_temp = (i + 1) % self.__cols
col = _temp if _temp else self.__cols
```

This code calculates which column (1-indexed) a subplot should be placed in, based on its index `i` (0-indexed) in the DataFrame.

#### Why This Logic is Necessary

- **Plotly uses 1-indexed columns**: Subplot columns are numbered starting from `1`, not `0`.
- **Modulo operation produces 0-indexed results**: The expression `(i + 1) % self.__cols` can yield `0`, which is invalid for Plotly.
- **Special case for the last column**: When `(i + 1)` is divisible by `self.__cols`, the modulo result is `0`. In this case, the subplot should actually be placed in the **last column** (column `self.__cols`).

```python
def _init_sub_graph_data(self):
    self._sub_graph_data = []
    self._subplot_titles = []

    for i, column_name in enumerate(self._df.columns):
        # Calculate row number
        row = math.ceil((i + 1) / self.__cols)

        # Calculate column number
        _temp = (i + 1) % self.__cols
        col = _temp if _temp else self.__cols

        # Generate display name (replace underscores with spaces)
        res_name = column_name.replace("_", " ")

        # Create subplot configuration tuple
        _temp_row_data = (
            column_name,  # Data column name
            dict(
                row=row,
                col=col,
                name=res_name,
                kind=self._kind_map["kind"],
                graph_kwargs=self._kind_map["kwargs"],
            ),
        )
        self._sub_graph_data.append(_temp_row_data)
        self._subplot_titles.append(res_name)
```

### Execution Example

**Assumptions**:
- `self._df` has 5 columns: `["IC", "Rank_IC", "FFR", "PA", "POS"]`
- `self.__cols = 2` (from `self._subplots_kwargs.get("cols", 2)`)
- `self._kind_map = {"kind": "ScatterGraph", "kwargs": {"mode": "lines"}}`

#### Calculation Process

| i | Column Name | Row Calculation | Col Calculation | Row | Col | Display Name |
|---|-------------|-----------------|-----------------|-----|-----|--------------|
| 0 | IC | ceil((0+1)/2)=1 | (1%2)=1 | 1 | 1 | "IC" |
| 1 | Rank_IC | ceil((1+1)/2)=1 | (2%2)=0 → 2 | 1 | 2 | "Rank IC" |
| 2 | FFR | ceil((2+1)/2)=2 | (3%2)=1 | 2 | 1 | "FFR" |
| 3 | PA | ceil((3+1)/2)=2 | (4%2)=0 → 2 | 2 | 2 | "PA" |
| 4 | POS | ceil((4+1)/2)=3 | (5%2)=1 | 3 | 1 | "POS" |

#### Generated `_sub_graph_data`

```python
[
    ("IC", {"row": 1, "col": 1, "name": "IC", "kind": "ScatterGraph", "graph_kwargs": {"mode": "lines"}}),
    ("Rank_IC", {"row": 1, "col": 2, "name": "Rank IC", "kind": "ScatterGraph", "graph_kwargs": {"mode": "lines"}}),
    ("FFR", {"row": 2, "col": 1, "name": "FFR", "kind": "ScatterGraph", "graph_kwargs": {"mode": "lines"}}),
    ("PA", {"row": 2, "col": 2, "name": "PA", "kind": "ScatterGraph", "graph_kwargs": {"mode": "lines"}}),
    ("POS", {"row": 3, "col": 1, "name": "POS", "kind": "ScatterGraph", "graph_kwargs": {"mode": "lines"}})
]
```

#### Generated `_subplot_titles`

```python
["IC", "Rank IC", "FFR", "PA", "POS"]
```

#### Resulting Layout

```
Row 1, Col 1     Row 1, Col 2
[IC Subplot]     [Rank IC Subplot]
  Title: IC         Title: Rank IC

Row 2, Col 1     Row 2, Col 2
[FFR Subplot]    [PA Subplot]
  Title: FFR        Title: PA

Row 3, Col 1     Row 3, Col 2
[POS Subplot]    [Empty]
  Title: POS
```

### Why This Method is Needed

## `_init_figure()` Method Explanation

**Source file**: [qlib/contrib/report/graph.py#L295](https://github.com/microsoft/qlib/blob/main/qlib/contrib/report/graph.py#L295)

This method is responsible for **creating the complete subplot figure** by assembling all the configured subplots, applying layout settings, and returning a Plotly figure object.

### Method Overview

```python
def _init_figure(self):
    # 1. Create an empty subplot grid
    # 2. Generate and add each subplot's traces to their positions
    # 3. Apply subplot-level layout settings (axis titles, etc.)
    # 4. Apply global layout settings (title, size, theme)
```

---

## Line-by-Line Explanation with Data Examples

### Step 1: Create the Subplot Grid

```python
self._figure = make_subplots(**self._subplots_kwargs)
```

This creates an empty figure with a grid of subplots based on the pre-configured parameters.

**Example `_subplots_kwargs`**:
```python
_subplots_kwargs = {
    "rows": 3,
    "cols": 2,
    "shared_xaxes": False,
    "shared_yaxes": False,
    "vertical_spacing": 0.1,
    "subplot_titles": ["IC", "Rank_IC", "FFR", "PA", "POS"]
}

# Result: Creates a 3x2 grid with 5 subplots (one empty cell)
```

---

### Step 2: Iterate Through Subplot Configurations

```python
for column_name, column_map in self._sub_graph_data:
```

Iterates through each subplot's configuration data.

**Example `_sub_graph_data`**:
```python
_sub_graph_data = [
    ("IC", {"row": 1, "col": 1, "name": "IC", "kind": "ScatterGraph", "graph_kwargs": {}}),
    ("Rank_IC", {"row": 1, "col": 2, "name": "Rank IC", "kind": "ScatterGraph", "graph_kwargs": {}}),
    ("FFR", {"row": 2, "col": 1, "name": "FFR", "kind": "ScatterGraph", "graph_kwargs": {}}),
    ("PA", {"row": 2, "col": 2, "name": "PA", "kind": "ScatterGraph", "graph_kwargs": {}}),
    ("POS", {"row": 3, "col": 1, "name": "POS", "kind": "ScatterGraph", "graph_kwargs": {}})
]
```

---

### Step 3: Handle Different Input Types for `column_name`

```python
if isinstance(column_name, go.Figure):
    # Case 1: User provided a complete Plotly Figure object
    _graph_obj = column_name
```

**Example**:
```python
# If user passed a pre-created figure
pre_fig = go.Figure(data=[go.Scatter(x=[1,2,3], y=[4,5,6], name="Pre-made")])
column_name = pre_fig
_graph_obj = column_name  # Use directly
```

```python
elif isinstance(column_name, str):
    # Case 2: Column name string - create a chart from data
    temp_name = column_map.get("name", column_name.replace("_", " "))
    kind = column_map.get("kind", self._kind_map.get("kind", "ScatterGraph"))
    _graph_kwargs = column_map.get("graph_kwargs", self._kind_map.get("kwargs", {}))
    
    _graph_obj = BaseGraph.get_instance_with_graph_parameters(
        kind,
        **dict(
            df=self._df.loc[:, [column_name]],
            name_dict={column_name: temp_name},
            graph_kwargs=_graph_kwargs,
        ),
    )
```

**Example for a string column**:
```python
# Input
column_name = "IC"
column_map = {
    "row": 1, "col": 1, 
    "name": "IC", 
    "kind": "ScatterGraph", 
    "graph_kwargs": {"mode": "lines"}
}

# Process:
temp_name = "IC"  # from column_map["name"]
kind = "ScatterGraph"
_graph_kwargs = {"mode": "lines"}

# Creates a ScatterGraph object that contains Plotly Scatter traces
```

```python
else:
    raise TypeError()
```

---

### Step 4: Extract Traces and Add to Subplot


    graph = ScatterGraph(df, name_dict={...}, layout={...}, graph_kwargs={...})
    
    ↓

    __init__()
      ├── self._df = df
      ├── self._layout = layout or {}
      ├── self._graph_kwargs = graph_kwargs or {}
      ├── self._name_dict = name_dict or {col:col for col in df.columns}
      ├── self._init_parameters()           # 设置 self._graph_type = "Scatter"
      └── self._init_data()                 # ★ 核心入口
    
          ↓
    
          _init_data()
            └── self.data = self._get_data()     # ★ 这里产生 trace 列表
    
                ↓
    
                _get_data()   （ScatterGraph 继承自 BaseGraph，使用父类的默认实现）
    
                  return [
                      go.Scatter(                     # 第一个 trace
                          x = df.index,
                          y = df["列1"],
                          name = name_dict["列1"],
                          **self._graph_kwargs
                      ),
                      go.Scatter(                     # 第二个 trace
                          x = df.index,
                          y = df["列2"],
                          name = name_dict["列2"],
                          **self._graph_kwargs
                      ),
                      ...                             # 每列对应一个 go.Scatter
                  ]

```python
row = column_map["row"]
col = column_map["col"]

_graph_data = getattr(_graph_obj, "data")
```

**Example of `_graph_data`** (from a ScatterGraph object with detailed traces):

```python
# ================== _graph_data for Subplot (row=1, col=1) ==================
# This subplot contains IC, IC Smoothed, and Benchmark traces

_graph_data_ic = [
    # Trace 1: IC line with markers
    go.Scatter(
        name='IC',
        x=['2023-01-01', '2023-01-02', '2023-01-03'],
        y=[0.10, 0.15, 0.12],
        mode='lines+markers',
        line=dict(color='blue', width=2),
        marker=dict(size=8, symbol='circle'),
        showlegend=True
    ),
    
    # Trace 2: IC Smoothed line (dashed)
    go.Scatter(
        name='IC Smoothed',
        x=['2023-01-01', '2023-01-02', '2023-01-03'],
        y=[0.11, 0.14, 0.13],
        mode='lines',
        line=dict(color='lightblue', width=1, dash='dash'),
        showlegend=True
    ),
]

# ================== _graph_data for Subplot (row=1, col=2) ==================
# This subplot contains only Rank IC trace

_graph_data_rank = [
    go.Scatter(
        name='Rank IC',
        x=['2023-01-01', '2023-01-02', '2023-01-03'],
        y=[0.12, 0.14, 0.11],
        mode='lines+markers',
        line=dict(color='red', width=2),
        marker=dict(size=8, symbol='square'),
        showlegend=True
    )
]

# ================== _graph_data for Subplot (row=2, col=1) ==================
# This subplot contains only FFR trace

_graph_data_ffr = [
    go.Scatter(
        name='FFR',
        x=['2023-01-01', '2023-01-02', '2023-01-03'],
        y=[0.95, 0.98, 0.92],
        mode='lines+markers',
        line=dict(color='green', width=2),
        marker=dict(size=8, symbol='diamond'),
        showlegend=True
    )
]
```

```python
# Optional cleanup (commented out):
# for _item in _graph_data:
#     _item.pop('xaxis', None)
#     _item.pop('yaxis', None)
```

```python
for _g_obj in _graph_data:
    self._figure.add_trace(_g_obj, row=row, col=col)
```

**Detailed examples of adding traces**:

```python
# For IC subplot (row=1, col=1) - adding multiple traces to the same subplot
self._figure.add_trace(
    go.Scatter(
        name='IC',
        x=['2023-01-01', '2023-01-02', '2023-01-03'],
        y=[0.10, 0.15, 0.12],
        mode='lines+markers',
        line=dict(color='blue', width=2),
        marker=dict(size=8, symbol='circle'),
        showlegend=True
    ),
    row=1, col=1
)

self._figure.add_trace(
    go.Scatter(
        name='IC Smoothed',
        x=['2023-01-01', '2023-01-02', '2023-01-03'],
        y=[0.11, 0.14, 0.13],
        mode='lines',
        line=dict(color='lightblue', width=1, dash='dash'),
        showlegend=True
    ),
    row=1, col=1
)

# For Rank_IC subplot (row=1, col=2)
self._figure.add_trace(
    go.Scatter(
        name='Rank IC',
        x=['2023-01-01', '2023-01-02', '2023-01-03'],
        y=[0.12, 0.14, 0.11],
        mode='lines+markers',
        line=dict(color='red', width=2),
        marker=dict(size=8, symbol='square'),
        showlegend=True
    ),
    row=1, col=2
)

# For FFR subplot (row=2, col=1)
self._figure.add_trace(
    go.Scatter(
        name='FFR',
        x=['2023-01-01', '2023-01-02', '2023-01-03'],
        y=[0.95, 0.98, 0.92],
        mode='lines+markers',
        line=dict(color='green', width=2),
        marker=dict(size=8, symbol='diamond'),
        showlegend=True
    ),
    row=2, col=1
)
```

---

### Step 5: Apply Subplot-Level Layout

```python
if self._sub_graph_layout is not None:
    for k, v in self._sub_graph_layout.items():
        self._figure["layout"][k].update(v)
```

**Example `_sub_graph_layout`**:
```python
_sub_graph_layout = {
    "xaxis": {"title": "Date", "tickangle": 45},
    "xaxis2": {"title": "Date", "tickangle": 45},
    "xaxis3": {"title": "Date", "tickangle": 45},
    "yaxis": {"title": "IC Value"},
    "yaxis2": {"title": "Rank IC Value"},
    "yaxis3": {"title": "FFR Value"}
}

# After applying:
# Subplot (1,1): x-axis title "Date" (45°), y-axis title "IC Value"
# Subplot (1,2): x-axis title "Date" (45°), y-axis title "Rank IC Value"
# Subplot (2,1): x-axis title "Date" (45°), y-axis title "FFR Value"
```

---

### Step 6: Apply Global Layout and Theme

```python
# Use Plotly 3.x default theme for compatibility
self._figure["layout"].update(template=None)

# Apply user's global layout settings
self._figure["layout"].update(self._layout)
```

**Example `self._layout`**:
```python
self._layout = {
    "title": "Model Performance Analysis",
    "width": 1200,
    "height": 800,
    "showlegend": True,
    "legend": {"x": 1, "y": 1, "bgcolor": "rgba(255, 255, 255, 0.5)"},
    "font": {"size": 12},
    "paper_bgcolor": "white",
    "plot_bgcolor": "#f8f9fa"
}
```

---

## Complete Execution Example

Assume we have:
- DataFrame with 3 columns: `["IC", "Rank_IC", "FFR"]`
- 2x2 grid (3 subplots, one empty)
- All using `ScatterGraph` with `mode="lines+markers"`

**Step-by-step execution**:

1. **Creates empty 2x2 subplot grid** with titles
2. **For each column**:
   - `IC` → creates `ScatterGraph` → extracts 1-3 traces → adds to (1,1)
   - `Rank_IC` → creates `ScatterGraph` → extracts traces → adds to (1,2)
   - `FFR` → creates `ScatterGraph` → extracts traces → adds to (2,1)
3. **Applies subplot axis settings**: x-axis titles "Date" with 45° rotation
4. **Sets theme** to Plotly 3.x default and applies global layout with title, size, etc.

**Final result**:
```
Row 1, Col 1                    Row 1, Col 2
[IC Line Plot with markers]      [Rank IC Line Plot with markers]
  Title: IC                        Title: Rank IC
  X: "Date" (45°)                  X: "Date" (45°)
  Y: "IC Value"                    Y: "Rank IC Value"

Row 2, Col 1                    Row 2, Col 2
[FFR Line Plot with markers]      [Empty]
  Title: FFR
  X: "Date" (45°)
  Y: "FFR Value"
```
