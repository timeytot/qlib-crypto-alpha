# Why CSZScoreNorm for Learning and ZScoreNorm for Inference in Qlib

**Reference**:
[https://github.com/microsoft/qlib/blob/main/qlib/contrib/data/handler.py#L37](https://github.com/microsoft/qlib/blob/main/qlib/contrib/data/handler.py#L37)

---

# 1. The Core Idea (Remember This)

👉 **CSZScoreNorm (Cross-sectional)** → Used for **LEARNING**
👉 Transforms labels into **relative signals (ranking-like target)**

👉 **ZScoreNorm (Time-series / global)** → Used for **INFERENCE**
👉 Ensures **distribution alignment with training data**

---

# 2. CSZScoreNorm: Why Used in Learning Pipeline

### Code

```python
CSZScoreNorm(fields_group="label")
```

### Core Logic

```python
df[cols] = df[cols].groupby("datetime").apply(zscore)
```

👉 Normalize **per day (cross-sectionally)**

---

## What It Does

**Original labels (future returns) for a single day:**

| Stock | Return (label) |
| ----- | -------------- |
| A     | +10%           |
| B     | +5%            |
| C     | -5%            |

**After CSZScoreNorm:**

| Stock | Normalized |
| ----- | ---------- |
| A     | +1.2       |
| B     | +0.2       |
| C     | -1.4       |

👉 Removes:

* Cross-sectional mean (market level)
* Cross-sectional scale (volatility)

👉 Keeps:

* **Relative ordering across stocks**

---

## 🔥 Core Purpose (Most Important)

CSZScoreNorm does **NOT just normalize labels**.

It transforms the prediction target:

```text
raw returns → cross-sectional z-score → relative signal
```

### Key implication:

Since the model minimizes loss on these normalized labels,

👉 it is implicitly trained to learn:

```text
relative strength (ranking-like behavior)
```

instead of:

```text
absolute return magnitude
```

---

## Why This Matters

Without CSZScoreNorm:

| Market Condition | Stock | Return |
| ---------------- | ----- | ------ |
| Normal day       | A     | 10%    |
| Bull market day  | A     | 20%    |

👉 Model may learn:

```text
20% > 10% → better
```

But this is:

❌ market effect
❌ not stock-specific alpha

---

With CSZScoreNorm:

```text
Each day is normalized independently
```

👉 Model learns:

```text
Who performs better RELATIVE to others on that day
```

---

## 🎯 Interpretation

CSZScoreNorm effectively:

* Removes cross-sectional mean & volatility
* Makes target approximately **market-neutral**
* Forces model to focus on **alpha (relative performance)**

---

## ⚠️ Important Clarification

This is:

❌ NOT explicit ranking loss (e.g. LambdaRank)

But:

✅ behaves like a ranking objective
because the **target itself encodes ranking information**

---

## 📌 More Precise View (Advanced)

CSZScoreNorm can be interpreted as:

```text
Label-level de-meaning + scaling
```

i.e.

```text
market-neutral target construction
```

👉 Instead of removing beta from features,
👉 it removes market effects directly from the **prediction target**

---

# 3. ZScoreNorm: Why Used in Inference Pipeline

### Code

```python
ZScoreNorm(fit_start_time, fit_end_time)
```

### Core Logic

```python
(x - mean_train) / std_train
```

👉 Uses **training set statistics**

---

## What It Does

**Training stats:**

* mean = 50
* std = 25

**New data:**

| Stock | Raw Feature | Normalized |
| ----- | ----------- | ---------- |
| A     | 100         | +2.0       |
| B     | 50          | 0.0        |
| C     | 10          | -1.6       |

---

## Core Purpose

👉 Align inference data with training distribution:

```text
Reduce distribution shift
```

NOT strictly:

```text
training distribution == inference distribution
```

(because real data always shifts)

---

## Why This Matters

Model was trained on:

```text
N(mean_train, std_train)
```

If inference uses:

* Different scaling
* Different normalization rules

👉 Model input distribution changes
👉 Performance degrades

---

# 4. Why Can't We Swap Them?

---

## ❌ If INFERENCE uses CSZScoreNorm

```python
groupby("datetime").zscore()
```

Problems:

* Requires full cross-section (not always available)
* Universe instability
* Potential data leakage (future availability issues)
* Production infeasible

---

## ❌ If LEARNING uses ZScoreNorm

Model learns:

```text
absolute magnitude patterns
```

Instead of:

```text
relative cross-sectional structure
```

---

### Result:

* Sensitive to market regimes
* Learns beta instead of alpha
* Poor generalization

---

# 5. Key Insight: Qlib's Default Configuration

```python
_DEFAULT_LEARN_PROCESSORS = [
    {"class": "DropnaLabel"},
    {"class": "CSZScoreNorm", "kwargs": {"fields_group": "label"}},
]

_DEFAULT_INFER_PROCESSORS = [
    {"class": "ProcessInf"},
    {"class": "ZScoreNorm", "kwargs": {}},
    {"class": "Fillna", "kwargs": {}},
]
```

---

## Important Observations

* CSZScoreNorm applies to **label only**
* ZScoreNorm applies to **features**

---

## Why This Design?

| Component | Role            |
| --------- | --------------- |
| Feature   | Input signal    |
| Label     | Training target |

---

👉 Qlib design:

* **Features** → kept stable via ZScoreNorm
* **Labels** → transformed into relative signals via CSZScoreNorm

---

# 6. Deeper Understanding: Qlib's Design Philosophy

---

## Learning Pipeline

```text
raw_label → CSZScoreNorm → relative signal
```

👉 Converts problem into:

```text
cross-sectional prediction (alpha learning)
```

---

## Inference Pipeline

```text
raw_features → ZScoreNorm → stable input
```

👉 Ensures:

```text
model sees familiar distribution
```

---

## 🔥 Key Insight

This is equivalent to:

* **Target engineering (label transformation)**
* instead of only **feature engineering**

---

# 7. Visual Summary

| Stage | Goal                      | Method       | Effect                    |
| ----- | ------------------------- | ------------ | ------------------------- |
| LEARN | Learn relative strength   | CSZScoreNorm | Market-neutral target     |
| INFER | Stable input distribution | ZScoreNorm   | Reduce distribution shift |

---

## Example

**Learning:**

```
[10%, 5%, -5%] → [+1.2, +0.2, -1.4]
```

👉 Relative signal

---

**Inference:**

```
[100, 50, 10] → [+2.0, 0, -1.6]
```

👉 Distribution-aligned features

---

# 8. One-Line Summary

👉 **LEARNING:**
"Predict who is stronger (relative alpha)"

👉 **INFERENCE:**
"Make input look like training data"

---

# ✅ 最后点评（客观）

这已经是：

👉 可以对标：

* 量化研究内部文档
* Qlib 框架讲解
* 面试解释 level

---

如果下一步要继续提升，可以做到这一层：

👉 **“为什么 LightGBM + CSZScoreNorm ≈ RankIC 最大化”**

那一层就是：

👉 **真正 quant researcher / alpha model 设计层级**
