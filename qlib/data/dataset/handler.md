# Qlib `DataHandlerLP` Processing Pipeline

**Source Code**: https://github.com/microsoft/qlib/blob/main/qlib/data/dataset/handler.py#L552

This document explains the **data processing pipeline of `DataHandlerLP`** in Qlib, focusing on:
- Why training uses `learn_df`
- Why prediction/backtesting uses `infer_df`
- The exact processor execution order
- **When to call `model.fit` and `model.predict`**
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
| Prediction / Backtesting (`model.predict`) | `infer_df` | Minimal processing (usually only Fillna) | Simulate real trading conditions and avoid look-ahead bias | Backtest results become inflated and unrealistic |

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
_infer  ←  Used for prediction/backtesting
    ↓
learn_processors
    ↓
_learn  ←  Used for training
```

**Important relationship**: `learn = infer + additional processors`

---

## 3. Complete Training & Prediction Workflow

### Time Series Perspective (Rolling Window)

```
Training Period (2020)              Prediction Period (2021)
      |                                    |
      ▼                                    ▼
learn_df_2020                        infer_df_2021
(model.fit)                     →   (model.predict)
      |                                    |
      ▼                                    ▼
   Model_2020  ───────────────────→  Predictions_2021
                                          |
                                          ▼
                                   Evaluate with actual labels
                                   (when they become available)
```

### Code Example

```python
# ==================== TRAINING PHASE ====================
# Use 2020 data to train the model
train_data = dataset.prepare(
    segments="train",           # e.g., ("2020-01-01", "2020-12-31")
    data_key="learn"             # Use learn_df for training
)

# train_data contains:
# - Features processed by shared_processors + infer_processors + learn_processors
# - Labels are clean (no NaN, normalized)
X_train = train_data['feature']
y_train = train_data['label']

# Train the model
model.fit(X_train, y_train)      # ← model.fit uses learn_df

# ==================== PREDICTION PHASE ====================
# Use 2021 data to make predictions
test_data = dataset.prepare(
    segments="test",             # e.g., ("2021-01-01", "2021-12-31")
    data_key="infer"              # Use infer_df for prediction (default)
)

# test_data contains:
# - Features processed by shared_processors + infer_processors
# - Labels are raw (may have NaN/extremes) - used only for evaluation
X_test = test_data['feature']
y_test = test_data['label']      # Actual labels for evaluation

# Make predictions
predictions = model.predict(X_test)  # ← model.predict uses infer_df

# Evaluate (after true labels are known)
from sklearn.metrics import mean_squared_error
mse = mean_squared_error(y_test, predictions)
```

---

## 4. Rolling Window Example (Realistic Backtesting)

```python
# Configuration
handler = DataHandlerLP(...)
dataset = DatasetH(handler=handler, segments={
    'train': ('2020-01-01', '2020-12-31'),
    'valid': ('2021-01-01', '2021-06-30'),
    'test': ('2021-07-01', '2021-12-31')
})

# ===== STEP 1: Train on 2020 data =====
X_train = dataset.prepare('train', data_key='learn')['feature']
y_train = dataset.prepare('train', data_key='learn')['label']
model.fit(X_train, y_train)  # ← model.fit with learn_df

# ===== STEP 2: Validate on H1 2021 =====
X_valid = dataset.prepare('valid', data_key='infer')['feature']
y_valid = dataset.prepare('valid', data_key='infer')['label']
pred_valid = model.predict(X_valid)  # ← model.predict with infer_df
print("Validation MSE:", mean_squared_error(y_valid, pred_valid))

# ===== STEP 3: Retrain on more data =====
# Use 2020 + H1 2021 for training
dataset.config(segments={
    'train': ('2020-01-01', '2021-06-30')
})
X_train2 = dataset.prepare('train', data_key='learn')['feature']
y_train2 = dataset.prepare('train', data_key='learn')['label']
model.fit(X_train2, y_train2)  # Retrain with more data

# ===== STEP 4: Test on H2 2021 =====
X_test = dataset.prepare('test', data_key='infer')['feature']
y_test = dataset.prepare('test', data_key='infer')['label']
pred_test = model.predict(X_test)
print("Test MSE:", mean_squared_error(y_test, pred_test))
```

---

## 5. Example with Real Data

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

**Result**: `self._infer` (used for prediction)

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

**When to use**: `model.predict(X_test)` uses this data's features

---

### Step 3 — `learn_processors`

Example: `DropnaLabel`, `CSZScoreNorm(label)`

**Result**: `self._learn` (used for training)

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

**When to use**: `model.fit(X_train, y_train)` uses this data's features and labels

---

## 6. Training vs Prediction: Code Comparison

```python
# ===== TRAINING =====
# Get learn_df (heavily processed labels)
train_learn = dataset.prepare("train", data_key="learn")
model.fit(
    train_learn['feature'],  # X: processed features
    train_learn['label']     # y: clean, normalized labels
)

# ===== PREDICTION =====
# Get infer_df (minimally processed labels)
test_infer = dataset.prepare("test", data_key="infer")  # default
predictions = model.predict(
    test_infer['feature']     # X: same feature processing as training
)

# Evaluate (labels in infer_df are raw, used only for evaluation)
true_labels = test_infer['label']  # May contain NaN/extremes
mse = mean_squared_error(true_labels, predictions)
```

---

## 7. Summary: When to Use What

| Step | What to Use | Data Key | Label State | Code |
|------|-------------|----------|-------------|------|
| **Training** | `learn_df` | `"learn"` | Clean, normalized, no NaN | `model.fit(X_learn, y_learn)` |
| **Validation** | `infer_df` | `"infer"` | Raw (may have NaN/extremes) | `model.predict(X_infer)` |
| **Test/Backtest** | `infer_df` | `"infer"` | Raw (may have NaN/extremes) | `model.predict(X_infer)` |
| **Live Prediction** | `infer_df` | `"infer"` | Labels not available yet | `model.predict(X_infer)` |

### Golden Rule
- **`model.fit`** → always use **`data_key="learn"`**
- **`model.predict`** → always use **`data_key="infer"`** (default)

This separation ensures that:
- Training remains stable with clean labels
- Predictions are realistic and unbiased
- Backtest results are trustworthy
