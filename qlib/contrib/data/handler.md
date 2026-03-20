# Why CSZScoreNorm for Learning and ZScoreNorm for Inference in Qlib

**Reference**: [https://github.com/microsoft/qlib/blob/main/qlib/contrib/data/handler.py#L37](https://github.com/microsoft/qlib/blob/main/qlib/contrib/data/handler.py#L37)

---

## 1. The Core Idea (Remember This)

👉 **CSZScoreNorm (Cross-sectional)** → Used for **LEARNING** → **"Removes market structure"**
👉 **ZScoreNorm (Time-series)** → Used for **INFERENCE** → **"Ensures distribution consistency"**

---

## 2. CSZScoreNorm: Why Used in Learning Pipeline

### Code
```python
CSZScoreNorm(fields_group="label")
```

### Core Logic
```python
df[cols] = df[cols].groupby("datetime").apply(zscore)
```
👉 Normalizes **per day** (cross-sectionally)

### What It Does

**Original labels (future returns) for a single day:**

| Stock | Return (label) |
|-------|----------------|
| A | +10% |
| B | +5% |
| C | -5% |

**After CSZScoreNorm:**

| Stock | Normalized |
|-------|------------|
| A | +1.2 |
| B | +0.2 |
| C | -1.4 |

👉 **Preserves only relative strength**

### Why Learning Needs This

You're solving a **stock selection / ranking problem** (cross-sectional problem).

**What the model should learn:**
- ❌ "What is the absolute return value?"
- ✅ **"Which stocks are stronger today?"**

### The Problem Without CSZScoreNorm

If you train on raw returns:

| Market Condition | Stock | Return |
|------------------|-------|--------|
| Normal day | A | 10% |
| Bull market day | A | 20% |

The model mistakenly learns: *"20% > 10% → A is better"*
But actually: **It's just the market getting stronger!**

👉 This is learning **market beta**, not **alpha**

### Core Purpose

Remove these noises:
- 📉 Market systematic risk
- 📊 Volatility changes
- 🌍 Macro environment shifts

Keep only:
✨ **Alpha (relative excess returns)**

---

## 3. ZScoreNorm: Why Used in Inference Pipeline

### Code
```python
ZScoreNorm(fit_start_time, fit_end_time)
```

### Core Logic
```python
(x - mean_train) / std_train
```
👉 Uses **training set statistics**

### What It Does

**Training period stats:**
- mean = 50
- std = 25

**New inference data:**

| Stock | Raw Feature | Normalized |
|-------|-------------|------------|
| A | 100 | +2.0 |
| B | 50 | 0.0 |
| C | 10 | -1.6 |

👉 Uses **historical training statistics**, not today's data

### Why Inference Needs This

The model was trained on a specific distribution:
```python
training distribution = N(mean_train, std_train)
```

If inference uses:
- ❌ New mean/std each day
- ❌ Cross-sectional normalization

👉 **Distribution shifts** → Model fails

### Core Purpose

Ensure:
✅ **Training distribution == Inference distribution**

---

## 4. Why Can't We Swap Them?

### ❌ If INFERENCE uses CSZScoreNorm

```python
# Wrong for inference
groupby("datetime").zscore()  # Uses all stocks from THAT day
```

**Problems in production:**
- Some stocks may be halted/delayed
- Universe is unstable
- Can't get complete cross-section in real trading
- 🚨 **Potential future information / data leakage**

### ❌ If LEARNING uses ZScoreNorm

The model learns **absolute magnitudes** instead of **relative rankings**.

Results:
- Sensitive to market regimes
- Poor generalization
- Can't separate alpha from beta

---

## 5. Key Insight: Qlib's Default Configuration

```python
_DEFAULT_LEARN_PROCESSORS = [
    {"class": "DropnaLabel"},
    {"class": "CSZScoreNorm", "kwargs": {"fields_group": "label"}},  # 👈 Only normalizes LABEL
]

_DEFAULT_INFER_PROCESSORS = [
    {"class": "ProcessInf"},
    {"class": "ZScoreNorm", "kwargs": {}},  # 👈 Normalizes FEATURES
    {"class": "Fillna", "kwargs": {}},
]
```

**Important observation:**
- CSZScoreNorm only applies to **label** in learning
- ZScoreNorm applies to **features** in inference

Why?
- **Features** → Used by model (keep original structure)
- **Label** → Training target (must be stable, comparable across days)

---

## 6. Deeper Understanding: Qlib's Design Philosophy

### Learning Pipeline
Transforms problem into a **cross-sectional ranking problem**
```python
raw_label → CSZScoreNorm → relative ranking
```

### Inference Pipeline
Transforms data into **model-acceptable distribution**
```python
raw_features → ZScoreNorm → stable distribution
```

### For Crypto/AI Strategy Context

**CSZScoreNorm = Factor de-Beta-ing**
```python
factor = raw_factor - market_mean
```
👉 Making it **market neutral**

**ZScoreNorm = Feature Engineering Standardization**
```python
features = (raw_features - train_mean) / train_std
```
👉 Making inputs **stable for the model**

---

## 7. Visual Summary

| Stage | Goal | Method | What it does |
|-------|------|--------|--------------|
| **LEARN** | Learn "who is stronger" (ranking) | **CSZScoreNorm** | Removes market beta, keeps alpha |
| **INFER** | Keep input distribution stable | **ZScoreNorm** | Uses training stats, prevents shift |

### With Example Data

**Learning (CSZScoreNorm):**
```
Day 1: [10%, 5%, -5%] → [+1.2, +0.2, -1.4]  # Relative strength only
```

**Inference (ZScoreNorm):**
```
Train stats: mean=50, std=25
New data: [100, 50, 10] → [+2.0, 0, -1.6]  # Stable distribution
```

---

## 8. One-Line Summary

👉 **LEARNING: "I only care who's stronger today"** (CSZScoreNorm)
👉 **INFERENCE: "Today's data must look like training data"** (ZScoreNorm)
