# Qlib Label Definition & `DropnaLabel` In-depth Analysis

> **Repository Reference**: [microsoft/qlib](https://github.com/microsoft/qlib)
> **Core Files**:
> *   [handler.py - Alpha158/360 Classes (Line 41)](https://github.com/microsoft/qlib/blob/main/qlib/contrib/data/handler.py#L41)
> *   [handler.py - DataHandlerLP Logic (Line 534)](https://github.com/microsoft/qlib/blob/main/qlib/data/dataset/handler.py#L534)
> *   [processor.py - DropnaLabel Definition (Line 109)](https://github.com/microsoft/qlib/blob/main/qlib/data/dataset/processor.py#L109)

This document provides a clear, structured explanation of Qlib's default label definition and the critical reason why the `DropnaLabel` processor cannot be used during inference.

## 1. The Default Label: `Ref($close, -2)/Ref($close, -1) - 1`

This expression is the core label for many built-in handlers like `Alpha158` and `Alpha360`.

### Understanding the `Ref` Function
In Qlib's expression engine, `Ref` shifts the data series:
*   `Ref(x, 1)`: Value of `x` from **yesterday** (t-1)
*   `Ref(x, 0)`: Value of `x` from **today** (t)
*   `Ref(x, -1)`: Value of `x` from **tomorrow** (t+1)
*   `Ref(x, -2)`: Value of `x` from **the day after tomorrow** (t+2)

### The Label Calculation in Plain English
The expression `Ref($close, -2)/Ref($close, -1) - 1` calculates a **forward return**. For a given day `t`:
```python
label(t) = close(t+2) / close(t+1) - 1
```
This represents the return from **tomorrow's close** to **the day after tomorrow's close**.

### Why This Specific Window? The Trading Logic
This definition isn't arbitrary; it respects the real-world constraints of trading, especially in markets with fixed trading sessions (like stocks).

1.  **Signal Generation at `t`**: At the end of day `t`, you have all the information (features) to generate a trading signal.
2.  **Earliest Execution at `t+1`**: You cannot trade at the closing price of `t`. The earliest you can execute a trade based on the signal is at the **open (or during) the next trading day, `t+1`**.
3.  **Holding Period**: If you hold the position for one full day, you will sell at the close of day **`t+2`**.

Therefore, the label correctly measures the **actionable forward return**: the return from the first possible entry point (`t+1` close) to the first possible exit point (`t+2` close).

### Concrete Example with Prices

Let's trace through a price series to see how the label is created and where it fails.

| Date (t) | Close Price | Calculation for Label(t) | Label Value (Return) |
| :--- | :--- | :--- | :--- |
| 1 | 100 | `close(3)/close(2) - 1` = `101/102 - 1` | **-0.0098** |
| 2 | 102 | `close(4)/close(3) - 1` = `105/101 - 1` | **0.0396** |
| 3 | 101 | `close(5)/close(4) - 1` = `110/105 - 1` | **0.0476** |
| 4 | 105 | `close(6)/close(5) - 1` = `?/110 - 1` | **`NaN`** |
| 5 | 110 | `close(7)/close(6) - 1` = `?/? - 1` | **`NaN`** |

As shown, the label for the last two data points is `NaN` because the future data required for calculation does not exist.

## 2. The `DropnaLabel` Processor

This processor is a standard part of the `_DEFAULT_LEARN_PROCESSORS` in Qlib.

### What It Does
Its function is simple: it removes any rows where the **label value** is `NaN`.
```python
# From processor.py (simplified)
class DropnaLabel(DropnaProcessor):
    def __init__(self, fields_group="label"):
        super().__init__(fields_group=fields_group)
    # ... other methods
```

Applied to the example above, it would delete the rows for `t=4` and `t=5`, keeping only the samples with valid labels for training.

### Why It Is NOT Usable for Inference (`is_for_infer() = False`)

This is the most critical point. The `DropnaLabel` class explicitly overrides the `is_for_infer()` method to return `False`:
```python
def is_for_infer(self) -> bool:
    """The samples are dropped according to label. So it is not usable for inference"""
    return False
```

Here is the step-by-step reasoning for why this is a fundamental safeguard against **look-ahead bias**.

#### 🚫 The Inference Problem: You Don't Know the Future
During inference (or "testing"), you are simulating a real-world scenario. At the current time `t`, you have no knowledge of `t+1` or `t+2`.

If `DropnaLabel` were allowed in the inference pipeline, here is what would happen:
1.  At `t=5`, your model wants to make a prediction. The data loader fetches features for `t=5`.
2.  The `DropnaLabel` processor checks the label column. It sees that `label(5)` is `NaN`.
3.  It **drops the row for `t=5`**, and no prediction is made.

This seems harmless at first glance. But ask the critical question: **How does the processor know that `label(5)` is `NaN`?**

It knows because **it has already peeked into the future** and realized that `close(6)` and `close(7)` do not exist. By using the *existence* of the future label as a filter for today's prediction, you are introducing a catastrophic look-ahead bias. You are effectively telling the model, "Only predict for days that we already know have a valid future return."

#### ⚠️ The Look-Ahead Bias
In a backtest, if you incorrectly include `DropnaLabel` in your inference processors, your strategy will only be evaluated on days that are at least 2 days before the end of your dataset. Your performance metrics will be **artificially inflated** because you've excluded the periods where you cannot trade (the end of the dataset), which in a real scenario would simply be your last few holdings.

## 3. Summary: Training vs. Inference

| Aspect | Training (`learn_processors`) | Inference (`infer_processors`) |
| :--- | :--- | :--- |
| **`DropnaLabel` Status** | ✅ **Allowed** | ❌ **Forbidden (by code)** |
| **Goal** | Clean the training dataset. Ensure the model only learns from examples with a defined forward return. | Make a prediction for *every* valid trading day, based *only* on information available up to that day. |
| **Action** | Drops rows with `NaN` labels. This is correct, as these samples lack a target to learn from. | Would drop rows where the *future* label is `NaN`. This is impossible to know in real-time. |
| **Risk** | None. This is standard data preparation. | **Fatal look-ahead bias**. It uses future information to filter the present. |

### Key Takeaway
`DropnaLabel` is a **training-only** processor. Its presence in the inference pipeline would violate the fundamental principle of time-series backtesting: never use information from the future to make a decision about the past. Qlib's design correctly enforces this by making the processor return `False` for `is_for_infer()`, causing an error if you try to use it in the wrong context.
