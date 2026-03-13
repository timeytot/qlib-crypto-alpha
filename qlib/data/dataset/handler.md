# Qlib `DataHandlerLP` Processing Pipeline

**Source Code**: https://github.com/microsoft/qlib/blob/main/qlib/data/dataset/handler.py#L552

This document explains the **data processing pipeline of `DataHandlerLP`** in Qlib, focusing on:
- Why training uses `learn_df`
- Why prediction/backtesting uses `infer_df`
- The exact processor execution order
- A simplified example with real data

Framework: **Qlib (Microsoft Quantitative Investment Platform)**

---

## 1. Why Training Uses `learn_df` and Prediction Uses `infer_df`

The design follows one fundamental principle:

> **Training prioritizes clean and stable labels, while prediction/backtesting must preserve realistic and unbiased labels.**

### Comparison

| Stage | Dataset | Label Processing | Purpose | If Reversed |
|-------|---------|------------------|---------|-------------|
| Model Training (`model.fit`) | `learn_df` | Heavy processing (DropnaLabel, RankNorm, Clip, etc.) | Stabilize training and improve label distribution | Training becomes unstable; model learns noise |
| Prediction / Backtesting | `infer_df` | Minimal processing (usually only Fillna) | Simulate real trading conditions and avoid look-ahead bias | Backtest results become inflated and unrealistic |

### Key Idea
- **Training**: labels can be aggressively cleaned to improve learning
- **Prediction**: labels must remain as close as possible to reality

---

## 2. Data Processing Pipeline (Default: `process_type = "append"`)

```
DataLoader
    ↓
raw_df (= self._data)
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

**Important relationship**: `learn = infer + additional processors`

---

## 3. Pipeline Structure (Conceptual)

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

#### `shared_processors`
Applied to all datasets. Typical tasks:
- Feature cleaning
- Normalization
- Feature filling

**Examples**: `DropnaFeature`, `RobustZScoreNorm`, `Fillna`

#### `infer_processors`
Used to produce **prediction/backtest data**. Rules:
- Do not modify labels in ways that require future information
- Avoid removing samples based on label values

**Typical operations**: `Fillna`, feature normalization

#### `learn_processors`
Executed **after `infer_processors`**, based on `_infer`. Used only for training.

**Typical operations**: `DropnaLabel`, `CSRankNorm(label)`, label clipping

---

## 4. Example with Real Data

Assume the raw dataset (`self._data`) contains 3 stocks across 2 days.

### Raw Data

| datetime   | instrument | $close | RSI10 | LABEL0 |
|------------|-----------|--------|-------|--------|
| 2023-01-03 | SH600000  | 10.1   | 55.2  | 0.0212 |
|            | SH600519  | 1500.0 | 62.1  | NaN    |
|            | SZ300750  | 200.0  | 48.9  | 999.99 |
| 2023-01-04 | SH600000  | 10.3   | 56.8  | 0.0198 |
|            | SH600519  | 1510.0 | 63.4  | -0.0123|
|            | SZ300750  | 205.0  | 50.1  | 0.0389 |

**Problems**: Missing labels, extreme label values

---

### Step 1 — `shared_processors`

Example processors: `RobustZScoreNorm`, `FillnaFeature`

**Effect**: Features normalized, labels unchanged

Output: `_shared_df`

---

### Step 2 — `infer_processors`

Example: `Fillna(label = 0)`

**Result**: `self._infer`

| datetime   | instrument | $close | RSI10 | LABEL0 |
|------------|-----------|--------|-------|--------|
| 2023-01-03 | SH600000  | -0.95  | -0.45 | 0.0212 |
|            | SH600519  | 1.20   | 1.10  | 0.0    |
|            | SZ300750  | -0.25  | -0.65 | 999.99 |
| 2023-01-04 | SH600000  | -0.93  | -0.42 | 0.0198 |
|            | SH600519  | 1.22   | 1.12  | -0.0123|
|            | SZ300750  | -0.23  | -0.62 | 0.0389 |

**Properties**:
- Extreme values remain
- No rows removed

**Usage**: Prediction, Backtesting, Evaluation

---

### Step 3 — `learn_processors`

Example: `DropnaLabel`, `CSZScoreNorm(label)`

#### 1. DropnaLabel
Removes rows where the original label was missing.

**Removed row**: `2023-01-03 SH600519`

#### 2. Cross-Sectional Z-Score on Labels
Labels normalized across instruments on the same date.

**Result**: `self._learn`

| datetime   | instrument | $close | RSI10 | LABEL0 |
|------------|-----------|--------|-------|--------|
| 2023-01-03 | SH600000  | -0.95  | -0.45 | -0.71  |
|            | SZ300750  | -0.25  | -0.65 | 1.41   |
| 2023-01-04 | SH600000  | -0.93  | -0.42 | -0.68  |
|            | SH600519  | 1.22   | 1.12  | -0.92  |
|            | SZ300750  | -0.23  | -0.62 | 1.18   |

**Properties**:
- No missing labels
- Stable distribution

**Usage**: Model training

---

## 5. Why `infer` Must Be Generated First

Many label processors require **future or cross-sectional information**.

**Example**: `CSRankNorm(label)` requires all labels for the same day. If applied during inference, future returns would be implicitly used, introducing **look-ahead bias**.

Therefore the correct order is:

```
shared_processors → infer_processors → _infer → learn_processors → _learn
```

---

## 6. Alternative Mode: `independent`

If configured as `process_type = "independent"`, the pipeline becomes:

```
_shared_df
    ├─ infer_processors → _infer
    └─ learn_processors → _learn
```

Both pipelines are independent. However, most official handlers (such as `Alpha158` and `Alpha360`) use the default `append` mode.

---

## 7. Core Implementation Logic

Simplified implementation from `handler.py`:

```python
_shared_df = self._run_proc_l(_shared_df, self.shared_processors, ...)

_infer_df = self._run_proc_l(_infer_df, self.infer_processors, ...)
self._infer = _infer_df

_learn_df = _infer_df.copy()
_learn_df = self._run_proc_l(_learn_df, self.learn_processors, ...)
self._learn = _learn_df
```

**Key insight**: `_learn` is built on top of `_infer`

---

## 8. Dataset Usage

| Purpose | Code |
|---------|------|
| Training | `dataset.prepare(..., data_key="learn")` |
| Prediction / Backtesting | `dataset.prepare(..., data_key="infer")` (default) |

---

## 9. Summary

The core design of `DataHandlerLP`:

```
shared_processors → infer_processors → _infer → learn_processors → _learn
```

**Key principle**:
- Training data may aggressively clean labels
- Prediction data must remain realistic

This separation ensures that:
- Training remains stable
- Backtesting remains unbiased
- The pipeline avoids look-ahead bias
