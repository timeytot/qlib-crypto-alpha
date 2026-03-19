## `deepcopy_basic_type` Function – Full Data Shape Before & After

https://github.com/microsoft/qlib/blob/main/qlib/utils/data.py#L38

The `deepcopy_basic_type` function creates **new container structures** (dict, list, tuple) while **sharing references** to their contents (primitives and complex objects). This enables fast, safe config duplication in Qlib without copying expensive objects like models or datasets.

### Original Config (before copy)

```python
class ExpensiveModel:
    def __init__(self, learning_rate=0.01):
        self.learning_rate = learning_rate

some_expensive_model = ExpensiveModel(learning_rate=0.01)

config = {
    "topk": 50,                                 # int (immutable primitive)
    "n_drop": 5,                                # int
    "signal": some_expensive_model,             # shared reference to model
    "params": {                                 # nested dict
        "horizon": 5,
        "alpha": 0.9
    },
    "labels": [                                 # list of str (immutable)
        "Ref($close, -2)/$close - 1",
        "Ref($close, -5)/$close - 1"
    ],
    "extra": (1.0, 2.0)                         # tuple (immutable)
}
```

Memory layout (simplified):

```
config @ 0xA (dict)
├── "topk" → 50 @ 0xB (int)
├── "n_drop" → 5 @ 0xC (int)
├── "signal" → model @ 0xD (shared object)
├── "params" → dict @ 0xE
│   ├── "horizon" → 5 @ 0xF (int)
│   └── "alpha" → 0.9 @ 0x10 (float)
├── "labels" → list @ 0x11
│   ├── 0 → str @ 0x12
│   └── 1 → str @ 0x13
└── "extra" → tuple @ 0x14
    ├── 0 → 1.0 @ 0x15 (float)
    └── 1 → 2.0 @ 0x16 (float)
```

### After `new_config = deepcopy_basic_type(config)`

```python
new_config = {
    "topk": 50,                                 # same int value (shared)
    "n_drop": 5,
    "signal": some_expensive_model,             # same model object (shared reference)
    "params": {                                 # NEW dict object
        "horizon": 5,
        "alpha": 0.9
    },
    "labels": [                                 # NEW list object
        "Ref($close, -2)/$close - 1",
        "Ref($close, -5)/$close - 1"
    ],
    "extra": (1.0, 2.0)                         # NEW tuple object
}
```

Memory layout after copy (simplified):

```
new_config @ 0x100 (NEW dict)
├── "topk" → 50 @ 0xB (same as original)
├── "n_drop" → 5 @ 0xC (same)
├── "signal" → model @ 0xD (same object!)
├── "params" → NEW dict @ 0x101
│   ├── "horizon" → 5 @ 0xF (shared)
│   └── "alpha" → 0.9 @ 0x10 (shared)
├── "labels" → NEW list @ 0x102
│   ├── 0 → str @ 0x12 (shared)
│   └── 1 → str @ 0x13 (shared)
└── "extra" → NEW tuple @ 0x103
    ├── 0 → 1.0 @ 0x15 (shared)
    └── 1 → 2.0 @ 0x16 (shared)
```

### Summary Table: Copied vs Shared

| Element Type | Copied? (New Object) | Shared? (Original Reference) | Memory Address Change? | Modification Impact on Original |
|--------------|---------------------|------------------------------|------------------------|----------------------------------|
| **Top-level dict** | Yes | No | Yes | Structure changes independent |
| **Nested dict ("params")** | Yes | No | Yes | Structure changes independent |
| **Nested list ("labels")** | Yes | No | Yes | Structure changes independent |
| **Nested tuple ("extra")** | Yes | No | Yes | Structure changes independent |
| **Primitives (int, float, str)** | No (immutable) | Yes | No | Reassignment → no impact |
| **Complex object (model)** | No | Yes | No | In-place changes → affects all |

### Modification Examples

**Modify primitive (int/float/str) → safe, no impact**
```python
new_config["topk"] = 30
# config["topk"] still 50
```

**Modify nested container → only affects new copy**
```python
new_config["params"]["horizon"] = 10
# config["params"]["horizon"] still 5
```

**Modify shared mutable object → affects both**
```python
new_config["signal"].learning_rate = 0.001
# config["signal"].learning_rate also becomes 0.001 (same object!)
```

**To avoid affecting original: reassign**
```python
new_config["signal"] = copy.deepcopy(some_expensive_model)  # explicit deep copy if needed
```

看起来你的Markdown渲染器不支持LaTeX数学公式。我来帮你转换成纯文本格式，保持内容不变：

---

# Robust Z-Score: Median Absolute Deviation (MAD) Explained

> **Source Code**: [qlib/utils/data.py - robust_zscore function (Line 24)](https://github.com/microsoft/qlib/blob/main/qlib/utils/data.py#L24)
> **Reference**: [Median Absolute Deviation - Wikipedia](https://en.wikipedia.org/wiki/Median_absolute_deviation)

This document provides a clear, step-by-step explanation of the Median Absolute Deviation (MAD) and how it's used in the `robust_zscore` function for robust statistical normalization.

## 1. What is MAD?

The **Median Absolute Deviation (MAD)** is a robust measure of statistical dispersion. It is defined as the median of the absolute deviations from the data's median.

### Mathematical Definition
For a univariate dataset X1, X2, ..., Xn:

MAD = median(|Xi - median(X)|)

### Intuitive Meaning
MAD answers the question: **"What is the typical distance of a data point from the middle value?"**

Unlike standard deviation, which squares deviations (making it sensitive to outliers), MAD uses absolute values and the median, making it **resistant to outliers**.

## 2. Step-by-Step Calculation in Code

The `robust_zscore` function implements MAD in three simple lines:

```python
def robust_zscore(x: pd.Series, zscore=False):
    x = x - x.median()           # Step 1: Center the data
    mad = x.abs().median()        # Step 2: Calculate MAD
    x = np.clip(x / mad / 1.4826, -3, 3)  # Step 3: Scale and clip
    # ... (optional second normalization)
    return x
```

Let's break down each step with a concrete example.

### Example Dataset
Consider the data: `[1, 2, 3, 4, 10]`

#### **Step 1: Center the Data** (`x = x - x.median()`)
- **Purpose**: Shift the data so the median becomes 0. This makes the "center" reference point zero for easier deviation calculation.
- **Mathematically**: X_centered = X - median(X)
- **Why?** The absolute deviation |Xi - median(X)| becomes |X_centered|.

```python
data = pd.Series([1, 2, 3, 4, 10])
median_val = data.median()  # = 3.0
centered = data - median_val  # = [-2, -1, 0, 1, 7]
```

#### **Step 2: Take Absolute Values** (`x.abs()`)
- **Purpose**: Focus on the **magnitude** of deviation, ignoring direction (whether the point is above or below the median).
- **Mathematically**: This implements the absolute part of |Xi - median(X)|.

```python
abs_dev = centered.abs()  # = [2, 1, 0, 1, 7]
```

#### **Step 3: Find the Median of Absolute Deviations** (`.median()`)
- **Purpose**: Get a "typical" deviation value that is robust to outliers.
- **Result**: This is the **MAD**.

```python
abs_dev_sorted = [0, 1, 1, 2, 7]
mad = pd.Series(abs_dev_sorted).median()  # = 1.0
```

✅ **MAD for this dataset = 1.0**

## 3. Why Multiply by 1.4826? The Mathematical Derivation

The magic number **1.4826** comes from making MAD a **consistent estimator** of the standard deviation (σ) for normally distributed data. Here's the derivation.

### Step 1: The Probabilistic Definition of MAD
For a symmetric distribution (like the normal distribution), the population MAD is defined such that **50% of the data falls within one MAD of the center**:

P(|X - μ| ≤ MAD) = 1/2

### Step 2: Standardize the Variable
Let Z = (X - μ)/σ ~ N(0,1), a standard normal variable. The condition becomes:

P(|Z| ≤ MAD/σ) = 1/2

### Step 3: Express Probability Using CDF
The probability |Z| ≤ a is the same as P(-a ≤ Z ≤ a). For a standard normal CDF Φ:

P(-a ≤ Z ≤ a) = Φ(a) - Φ(-a)

Using the symmetry property Φ(-a) = 1 - Φ(a), we get:

Φ(a) - (1 - Φ(a)) = 2Φ(a) - 1

### Step 4: Set the Probability to 1/2
We require 2Φ(a) - 1 = 1/2. Solving:

2Φ(a) = 3/2  ⇒  Φ(a) = 3/4

### Step 5: Find the Quantile
Thus, a = Φ⁻¹(3/4). The 75th percentile of the standard normal distribution is:

Φ⁻¹(0.75) ≈ 0.67449

### Step 6: Relate a to MAD and σ
Since a = MAD/σ, we have:

MAD/σ = 0.67449  ⇒  MAD = 0.67449 · σ

### Step 7: Solve for the Scale Factor k
To estimate σ from MAD, we want σ̂ = k · MAD. Substituting:

σ = MAD / 0.67449  ⇒  k = 1 / 0.67449 ≈ 1.4826
