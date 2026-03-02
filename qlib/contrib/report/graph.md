## Understanding `SubplotsGraph` Default Layout Initialization

**Source file**: [qlib/contrib/report/graph.py#L295](https://github.com/microsoft/qlib/blob/main/qlib/contrib/report/graph.py#L295)

The following code snippets are core parts of the `_init_subplots_kwargs()` and `_init_sub_graph_data()` methods. They are used to **calculate and set the default parameters for the subplot grid** when the user does not provide custom layout configurations.

### 1. Calculating the Number of Rows (`_init_subplots_kwargs`)

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

| Scenario | User Action | Result |
|----------|-------------|--------|
| **Custom Layout** | Provide `sub_graph_data` | Uses user-specified positions and chart types |
| **Default Layout** | `sub_graph_data=None` | Automatically calculates positions and uses default chart types |
