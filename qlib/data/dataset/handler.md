```markdown
# Qlib `DataHandlerLP` Processing Pipeline

**Source Code**  
https://github.com/microsoft/qlib/blob/main/qlib/data/dataset/handler.py#L552

This document explains the **data processing pipeline of `DataHandlerLP`** in Qlib, focusing on:

- Why training uses `learn_df`
- Why prediction/backtesting uses `infer_df`
- The exact processor execution order
- A simplified example with real data

Framework: **Qlib (Microsoft Quantitative Investment Platform)**

---

# 1. Why Training Uses `learn_df` and Prediction Uses `infer_df`

The design follows one fundamental principle:

> **Training prioritizes clean and stable labels, while prediction/backtesting must preserve realistic and unbiased labels.**

### Comparison

| Stage | Dataset | Label Processing | Purpose | If Reversed |
|------|--------|-----------------|--------|-------------|
| Model Training (`model.fit`) | `learn_df` | Heavy processing (DropnaLabel, RankNorm, Clip, etc.) | Stabilize training and improve label distribution | Training becomes unstable; model learns noise |
| Prediction / Backtesting | `infer_df` | Minimal processing (usually only Fillna) | Simulate real trading conditions and avoid look-ahead bias | Backtest results become inflated and unrealistic |

### Key Idea

- **Training:** labels can be aggressively cleaned to improve learning.
- **Prediction:** labels must remain as close as possible to reality.

---

# 2. Data Processing Pipeline

Default mode:

```

process_type = "append"

```

The full pipeline:

```

DataLoader
↓
raw_df  (= self._data)

↓
shared_processors
↓
_shared_df

↓
infer_processors
↓
_infer

↓
learn_processors
↓
_learn

```

Important relationship:

```

learn = infer + additional processors

```

---

# 3. Pipeline Structure (Conceptual)

```

(self._data)
│
▼
[shared_processors]
│
▼
(_shared_df)
│
├─[infer_processors]──► (_infer)
│
└─[infer_processors]──► (_infer_temp)
│
▼
[learn_processors]
│
▼
(_learn)

```

### Processor Roles

**shared_processors**

Applied to all datasets.

Typical tasks:

- Feature cleaning
- Normalization
- Feature filling

Examples:

```

DropnaFeature
RobustZScoreNorm
Fillna

```

---

**infer_processors**

Used to produce **prediction/backtest data**.

Rules:

- Do not modify labels in ways that require future information
- Avoid removing samples based on label values

Typical operations:

```

Fillna
Feature normalization

```

---

**learn_processors**

Executed **after `infer_processors`**, based on `_infer`.

Used only for training.

Typical operations:

```

DropnaLabel
CSRankNorm(label)
Label clipping

```

---

# 4. Example with Real Data

Assume the raw dataset (`self._data`) contains 3 stocks across 2 days.

### Raw Data

| datetime | instrument | $close | RSI10 | LABEL0 |
|--------|-----------|-------|------|-------|
|2023-01-03|SH600000|10.1|55.2|0.0212|
| |SH600519|1500.0|62.1|NaN|
| |SZ300750|200.0|48.9|999.99|
|2023-01-04|SH600000|10.3|56.8|0.0198|
| |SH600519|1510.0|63.4|-0.0123|
| |SZ300750|205.0|50.1|0.0389|

Problems in the dataset:

```

Missing labels
Extreme label values

```

---

## Step 1 — shared_processors

Example processors:

```

RobustZScoreNorm
FillnaFeature

```

Effect:

- Features normalized
- Labels unchanged

Output:

```

_shared_df

```

---

## Step 2 — infer_processors

Example:

```

Fillna(label = 0)

```

Result:

`self._infer`

| datetime | instrument | $close | RSI10 | LABEL0 |
|--------|-----------|-------|------|-------|
|2023-01-03|SH600000|-0.95|-0.45|0.0212|
| |SH600519|1.20|1.10|0.0|
| |SZ300750|-0.25|-0.65|999.99|

Properties:

```

Extreme values remain
No rows removed

```

Usage:

```

Prediction
Backtesting
Evaluation

```

---

## Step 3 — learn_processors

Example:

```

DropnaLabel
CSZScoreNorm(label)

```

Processing:

### Step 1 — DropnaLabel

Removes rows where the original label was missing.

Removed row:

```

2023-01-03 SH600519

```

### Step 2 — Cross-Sectional Z-Score

Labels normalized across instruments on the same date.

Example output:

| datetime | instrument | LABEL0 |
|--------|-----------|-------|
|2023-01-03|SH600000|-0.71|
| |SZ300750|1.41|

Properties:

```

No missing labels
Stable distribution

```

Usage:

```

Model training

```

---

# 5. Why `infer` Must Be Generated First

Many label processors require **future or cross-sectional information**.

Example:

```

CSRankNorm(label)

```

This requires:

```

All labels for the same day

```

If applied during inference:

```

Future returns would be implicitly used

```

This introduces **look-ahead bias**.

Therefore the correct order is:

```

shared_processors
↓
infer_processors
↓
_infer
↓
learn_processors
↓
_learn

```

---

# 6. Alternative Mode: `independent`

If configured as:

```

process_type = "independent"

```

The pipeline becomes:

```

_shared_df
├─ infer_processors → _infer
└─ learn_processors → _learn

```

Both pipelines are independent.

However most official handlers (such as `Alpha158` and `Alpha360`) use the default:

```

append

````

---

# 7. Core Implementation Logic

Simplified implementation:

```python
_shared_df = run(shared_processors)

_infer_df = _shared_df.copy()
_infer_df = run(infer_processors)
self._infer = _infer_df

_learn_df = _infer_df.copy()
_learn_df = run(learn_processors)
self._learn = _learn_df
````

Key insight:

```
_learn is built on top of _infer
```

---

# 8. Dataset Usage

Training:

```python
dataset.prepare(..., data_key="learn")
```

Prediction / Backtesting:

```python
dataset.prepare(..., data_key="infer")
```

---

# 9. Summary

The core design of `DataHandlerLP`:

```
shared_processors
      ↓
infer_processors
      ↓
_infer
      ↓
learn_processors
      ↓
_learn
```

Key principle:

```
Training data may aggressively clean labels
Prediction data must remain realistic
```

This separation ensures that:

* Training remains stable
* Backtesting remains unbiased
* The pipeline avoids look-ahead bias

```
```
