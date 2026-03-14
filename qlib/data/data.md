# Understanding Qlib's Data Provider System: Wrapper + `register_wrapper` Mechanism
## Key Code References

- [`qlib/data/data.py#L1331`](https://github.com/microsoft/qlib/blob/main/qlib/data/data.py#L1331): `register_wrapper(D, C.provider, "qlib.data")`
- [`qlib/config.py#L142`](https://github.com/microsoft/qlib/blob/main/qlib/config.py#L142): `"provider": "LocalProvider",`
- [`qlib/utils/__init__.py#L865`](https://github.com/microsoft/qlib/blob/main/qlib/utils/__init__.py#L865): `self._provider = provider`

This document explains the core design pattern behind Qlib's data access system, specifically how the `Wrapper` class and `register_wrapper` function work together to enable lazy initialization of data providers.

## Core Mechanism: Wrapper + `register_wrapper`

The `Wrapper` class is a proxy/delegate pattern implementation. Its sole purpose is to delay the actual instantiation of providers until `qlib.init()` is called, while allowing users to call methods (like `D.features()`, `D.instruments()`) directly on the wrapper object as if it were the real provider.

```python
class Wrapper:
    def __init__(self):
        self._provider = None

    def register(self, provider):
        self._provider = provider   # ← Here: assign the real instance

    def __getattr__(self, key):
        if self._provider is None:
            raise AttributeError("Please run qlib.init() first")
        return getattr(self._provider, key)  # ← Delegate all calls to the real provider
```

## What does `register_wrapper(D, C.provider, "qlib.data")` do?

In `register_all_wrappers(C)` ([`data.py#L1331`](https://github.com/microsoft/qlib/blob/main/qlib/data/data.py#L1331)):

```python
register_wrapper(D, C.provider, "qlib.data")
```

This line performs the following:
1. `C.provider` is a config (e.g., `"LocalProvider"` or a full config dict) — see [`config.py#L142`](https://github.com/microsoft/qlib/blob/main/qlib/config.py#L142)
2. `init_instance_by_config(C.provider, ...)` creates the actual instance (e.g., a `LocalProvider()` object)
3. `register_wrapper(...)` calls `D.register(that_instance)`, which executes:
   ```python
   D._provider = local_provider_instance
   ```

## Result: What is `D` after `qlib.init()`?

- `D` is an instance of `Wrapper`
- It has all the methods of `BaseProvider` (e.g., `.features()`, `.instruments()`, `.calendar()`) because `LocalProvider` inherits from `BaseProvider`
- When you call `D.features(...)`, it actually forwards the call to `D._provider.features(...)` via `__getattr__`

So yes: **`D` itself is a `Wrapper`, but behaves exactly like a `BaseProvider`** because all method calls are delegated to the real provider instance stored in `D._provider`.

## In a Nutshell: Type Hints vs. Runtime Reality

`BaseProvider` in the type hint is purely for static type checking and IDE support:

- It tells tools like `mypy`, PyCharm, or VS Code: "Even though the object is a `Wrapper`, you can safely assume it has all the methods and behavior of `BaseProvider` (e.g., `.features()`, `.instruments()`, `.calendar()`)."
- At runtime, this type annotation has zero effect — Python ignores `Annotated` completely during execution.

### Runtime Reality

The actual object at runtime is always an instance of `Wrapper`:

```python
D = Wrapper()                  # ← Real object in memory
isinstance(D, Wrapper)         # → True
isinstance(D, BaseProvider)    # → False (it's not a subclass)
```

The real functionality comes from `D._provider` ([`utils/__init__.py#L865`](https://github.com/microsoft/qlib/blob/main/qlib/utils/__init__.py#L865)):

After `qlib.init()`:
```python
D._provider = LocalProvider()  # (or ClientProvider, etc.)
```

This `_provider` is a concrete subclass of `BaseProvider`, so it implements all the actual methods.

When you call:
```python
D.features(...)
```

→ `Wrapper.__getattr__` forwards it to:
```python
D._provider.features(...)
```

## Summary

| Aspect | What it is | Runtime impact? |
|--------|------------|-----------------|
| Type hint | `Annotated[BaseProvider, Wrapper]` | None (only for static analysis) |
| Actual object | `Wrapper()` instance | Yes — this is what exists |
| Real implementation | `D._provider` (e.g., `LocalProvider()` instance) | Yes — this does the real work |

## Conclusion in One Sentence

`BaseProvider` in the annotation is just a type hint for better developer experience (autocomplete, error checking) and has no runtime effect. The real object is a `Wrapper`, and the actual `BaseProvider` functionality lives in the delegated `_provider` instance.

# Understanding `expr.load()` in Qlib: A Deep Dive into Expression Evaluation

This document explains the execution flow of `expr.load()` in Qlib, using the expression `Mean($close, 5) > $open` as an example.

## Reference Implementation

The code discussed in this document can be found in the Qlib repository:
- [qlib/data/data.py#L615](https://github.com/microsoft/qlib/blob/main/qlib/data/data.py#L615) - obj[field] = ExpressionD.expression(inst, field, start_time, end_time, freq)
- [qlib/data/data.py#L844](https://github.com/microsoft/qlib/blob/main/qlib/data/data.py#L844) - expression = self.get_expression_instance(field)
- [qlib/data/data.py#L859](https://github.com/microsoft/qlib/blob/main/qlib/data/data.py#L859) - series = expression.load(instrument, query_start, query_end, freq)
- [qlib/data/data.py#L397](https://github.com/microsoft/qlib/blob/main/qlib/data/data.py#L397) - expression = eval(parse_field(field))
- [qlib/data/data.py#L923](https://github.com/microsoft/qlib/blob/main/qlib/data/data.py#L923) - data = self.dataset_processor(instruments_d, column_names, start_time, end_time, freq, inst_processors=inst_processors)

## 1. Building the Expression Object Tree

First, the user input string is parsed and evaluated into an expression object tree:

```python
# User input
field = "Mean($close, 5) > $open"

# After eval(parse_field(field)), we get:
expr = Gt(                # Root node: Greater Than operator
    left=Mean(            # Left child: Mean operator
        feature=Feature('close'),  # Leaf node: close price feature
        N=5
    ),
    right=Feature('open') # Right child: open price feature
)
```

## 2. Calling `expr.load()`

```python
series = expr.load(
    instrument="SH600000",
    start_index=100,
    end_index=200,
    freq="day"
)
```

## 3. Execution Flow (Based on Class Hierarchy)

### Step 1: `Gt._load_internal()` - Located in `Gt` Class

```python
# Gt inherits from NpPairOperator
class Gt(NpPairOperator):
    def __init__(self, feature_left, feature_right):
        super(Gt, self).__init__(feature_left, feature_right, "greater")

# NpPairOperator's _load_internal
def _load_internal(self, instrument, start_index, end_index, *args):
    # 1. Load left operand
    if isinstance(self.feature_left, Expression):
        series_left = self.feature_left.load(instrument, start_index, end_index, *args)
        # Here self.feature_left is a Mean object
    
    # 2. Load right operand
    if isinstance(self.feature_right, Expression):
        series_right = self.feature_right.load(instrument, start_index, end_index, *args)
        # Here self.feature_right is a Feature('open') object
    
    # 3. Perform greater-than comparison
    res = np.greater(series_left, series_right)
    return res
```

### Step 2: `Mean._load_internal()` - Located in `Mean` Class

```python
# Mean inherits from Rolling
class Mean(Rolling):
    def __init__(self, feature, N):
        super(Mean, self).__init__(feature, N, "mean")

# Rolling class's _load_internal
def _load_internal(self, instrument, start_index, end_index, *args):
    # 1. Load underlying feature data
    series = self.feature.load(instrument, start_index, end_index, *args)
    # Here self.feature is a Feature('close') object
    
    # 2. Calculate rolling mean
    if isinstance(self.N, int) and self.N == 0:
        series = series.expanding(min_periods=1).mean()
    elif isinstance(self.N, float) and 0 < self.N < 1:
        series = series.ewm(alpha=self.N, min_periods=1).mean()
    else:
        series = series.rolling(self.N, min_periods=1).mean()
        # self.N = 5, so calculate 5-day moving average
    
    return series
```

### Step 3: `Feature._load_internal()` - Located in `Feature` Class

```python
# Feature inherits from Expression
class Feature(Expression):
    def _load_internal(self, instrument, start_index, end_index, freq):
        # Call the data provider
        return FeatureD.feature(
            instrument,     # "SH600000"
            str(self),      # "$close"
            start_index,    # 100 (but note Mean may require extension)
            end_index,      # 200
            freq            # "day"
        )
```

## 4. Complete Recursive Call Chain

```
Gt.load(100,200)
    │
    ├─ Gt._load_internal(100,200)
    │   │
    │   ├─ Mean.load(100,200)
    │   │   │
    │   │   ├─ Mean._load_internal(100,200)
    │   │   │   │
    │   │   │   ├─ Feature('close').load(96,200)  # Mean needs 4 previous days
    │   │   │   │   │
    │   │   │   │   └─ FeatureD.feature(96,200)   # Read close price data
    │   │   │   │
    │   │   │   └─ rolling(window=5).mean()       # Calculate 5-day MA
    │   │   │
    │   │   └─ Return Mean result (100-200)
    │   │
    │   ├─ Feature('open').load(100,200)
    │   │   │
    │   │   └─ FeatureD.feature(100,200)          # Read open price data
    │   │
    │   └─ np.greater()                            # Compare values
    │
    └─ Return boolean series (100-200)
```

## Final Returned Data

```python
# Example result
# Date        Mean($close,5) > $open
# 2020-01-01  True    # 5-day MA > open price
# 2020-01-02  False   # 5-day MA <= open price
# 2020-01-03  True
# ...
```

This execution flow demonstrates how Qlib decomposes complex expression calculations into individual operator implementations through **recursive calls** and **object-oriented polymorphism**. Each operator class implements its own `_load_internal` method, and the expression tree is evaluated recursively from the root down to the leaf nodes.
