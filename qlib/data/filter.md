# Understanding `_getFilterSeries()` in Qlib: Expression-Based Dynamic Filtering

This document explains the execution flow of `_getFilterSeries()` in Qlib, which is a key method for expression-based dynamic filtering of instruments.

## Reference Implementation

The code discussed in this document can be found in the Qlib repository:
- [qlib/data/filter.py#L341](https://github.com/microsoft/qlib/blob/main/qlib/data/filter.py#L341) - `ExpressionDFilter._getFilterSeries()`

## Method Overview

```python
def _getFilterSeries(self, instruments, fstart, fend):
    # do not use dataset cache
    try:
        _features = DatasetD.dataset(
            instruments,
            [self.rule_expression],
            fstart,
            fend,
            freq=self.filter_freq,
            disk_cache=0,
        )
```

### Input Parameters Example

```python
instruments = {
    'SH600000': [('2020-01-01', '2020-03-31'), ('2020-06-01', '2020-12-31')],
    'SH600004': [('2020-01-01', '2020-12-31')],
    'SZ000001': [('2020-01-01', '2020-12-31')],
}
fstart = '2020-02-01'                 # Filter start time
fend = '2020-11-30'                   # Filter end time
self.rule_expression = '$close > 100'  # Filter expression
self.filter_freq = 'day'               # Data frequency
```

## Execution Flow

### Step 1: Calling `DatasetD.dataset()`

`DatasetD` is a wrapper for `DatasetProvider`, which calls `LocalDatasetProvider.dataset()`:

```python
# Inside LocalDatasetProvider.dataset()
def dataset(self, instruments, fields, start_time, end_time, freq, inst_processors=[]):
    # 1. Normalize instruments format
    instruments_d = self.get_instruments_d(instruments, freq)
    # Result: maintains original dictionary format
    
    # 2. Get column names
    column_names = self.get_column_names(['$close > 100'])
    # Result: ['$close > 100']
    
    # 3. Align time to calendar
    if self.align_time:
        cal = Cal.calendar(start_time='2020-02-01', end_time='2020-11-30', freq='day')
        # cal = ['2020-02-01', '2020-02-02', ..., '2020-11-30']
        start_time = cal[0]   # '2020-02-01'
        end_time = cal[-1]    # '2020-11-30'
    
    # 4. Call dataset_processor for parallel processing
    data = self.dataset_processor(
        instruments_d,        # Dictionary of instruments
        column_names,         # ['$close > 100']
        start_time,           # '2020-02-01'
        end_time,             # '2020-11-30'
        freq,                 # 'day'
        inst_processors=[]    # No processors
    )
    return data
```

### Step 2: `dataset_processor()` - Parallel Processing

```python
@staticmethod
def dataset_processor(instruments_d, column_names, start_time, end_time, freq, inst_processors=[]):
    # 1. Determine number of parallel workers
    workers = max(min(C.get_kernels(freq), len(instruments_d)), 1)
    
    # 2. Create tasks for each instrument
    task_l = []
    for inst, spans in instruments_d.items():
        task_l.append(
            delayed(DatasetProvider.inst_calculator)(
                inst,                    # 'SH600000'
                start_time,              # '2020-02-01'
                end_time,                # '2020-11-30'
                freq,                    # 'day'
                column_names,            # ['$close > 100']
                spans,                   # Instrument's valid time spans
                C,                       # Configuration
                inst_processors          # []
            )
        )
    
    # 3. Execute tasks in parallel
    data = dict(zip(instruments_d.keys(), ParallelExt(...)(task_l)))
    
    # 4. Merge results
    new_data = {inst: data[inst] for inst in sorted(data.keys()) if len(data[inst]) > 0}
    data = pd.concat(new_data, names=["instrument"])
    
    return data
```

### Step 3: `inst_calculator()` - Single Instrument Processing

Using `SH600000` as an example:

```python
@staticmethod
def inst_calculator(inst='SH600000', start_time='2020-02-01', end_time='2020-11-30', 
                    freq='day', column_names=['$close > 100'], spans=None, ...):
    
    # 1. Calculate each expression
    obj = {}
    for field in column_names:  # field = '$close > 100'
        # Call ExpressionD.expression()
        obj[field] = ExpressionD.expression(
            inst,           # 'SH600000'
            field,          # '$close > 100'
            start_time,     # '2020-02-01'
            end_time,       # '2020-11-30'
            freq            # 'day'
        )
    
    # 2. Convert to DataFrame
    data = pd.DataFrame(obj)
    
    # 3. Handle index (if needed)
    if not data.empty and not np.issubdtype(data.index.dtype, np.dtype("M")):
        _calendar = Cal.calendar(freq='day')
        data.index = _calendar[data.index.values.astype(int)]
    
    # 4. Apply time span filtering
    if not data.empty and spans is not None:
        mask = np.zeros(len(data), dtype=bool)
        for begin, end in spans:
            mask |= (data.index >= begin) & (data.index <= end)
        data = data[mask]
    
    return data
```

### Step 4: `ExpressionD.expression()` - Expression Calculation

```python
# Inside ExpressionD.expression()
def expression(self, instrument='SH600000', field='$close > 100', 
               start_time='2020-02-01', end_time='2020-11-30', freq='day'):
    
    # 1. Parse the expression
    expression = self.get_expression_instance('$close > 100')
    # Returns: Gt(Feature('close'), 100) object
    
    # 2. Locate time indices
    _, _, start_index, end_index = Cal.locate_index(
        start_time, end_time, freq='day', future=False
    )
    # Assume start_index=40, end_index=180
    
    # 3. Get required extended window size
    lft_etd, rght_etd = expression.get_extended_window_size()
    # For '$close > 100', no extension needed: lft_etd=0, rght_etd=0
    query_start = max(0, start_index - lft_etd)  # 40
    query_end = end_index + rght_etd              # 180
    
    # 4. Load expression data
    series = expression.load(instrument, query_start, query_end, freq)
    # Returns Feature('close') data for indices 40-180
    # Then performs > 100 comparison
    
    # 5. Slice to requested range
    if not series.empty:
        series = series.loc[start_index:end_index]  # 40-180
    
    return series
```

### Step 5: Recursive `load()` Calls on Expression Objects

For `Gt(Feature('close'), 100)`:

```python
# Gt._load_internal()
def _load_internal(self, instrument, start_index, end_index, *args):
    # 1. Load left operand (Feature('close'))
    series_left = self.feature_left.load(instrument, start_index, end_index, *args)
    # Returns close price series
    
    # 2. Right operand is constant 100
    series_right = 100
    
    # 3. Perform greater-than comparison
    return np.greater(series_left, series_right)
    # Returns boolean series
```

```python
# Feature._load_internal()
def _load_internal(self, instrument, start_index, end_index, freq):
    # Call FeatureD.feature() to load data from disk
    return FeatureD.feature(
        instrument,     # 'SH600000'
        str(self),      # '$close'
        start_index,    # 40
        end_index,      # 180
        freq            # 'day'
    )
    # Returns close price Series
```

### Step 6: Return Result

After all instruments are processed, `_getFilterSeries` returns:

```python
_all_filter_series = {
    'SH600000': pd.Series(
        index=['2020-02-01', '2020-02-02', ...],
        data=[False, True, False, True, ...],  # $close > 100 results
        name='$close > 100'
    ),
    'SH600004': pd.Series(
        index=['2020-02-01', '2020-02-02', ...],
        data=[False, False, False, False, ...],
        name='$close > 100'
    ),
    'SZ000001': pd.Series(
        index=['2020-02-01', '2020-02-02', ...],
        data=[True, True, False, True, ...],
        name='$close > 100'
    ),
}
```

## Key Points Summary

1. **`disk_cache=0`**: Bypasses disk cache, loading data directly from the source
2. **Parallel Processing**: Multiple instruments are processed simultaneously for efficiency
3. **Recursive Calls**: Expression trees are evaluated recursively from root to leaves
4. **Time Alignment**: Automatically aligns to calendar to ensure data consistency
5. **Time Span Filtering**: Only retains data within each instrument's valid time periods
6. **Return Format**: Dictionary `{instrument_code: boolean_series}` indicating whether each instrument satisfies the filter condition on each day
