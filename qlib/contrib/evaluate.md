# Information ratio

https://github.com/microsoft/qlib/blob/main/qlib/contrib/evaluate.py#L85

These two formulas are **mathematically identical**!

### Proof

```python
# Formula 1: Annualized Information Ratio = Annualized Return / Annualized Std Dev
Annualized Return = μ × N
Annualized Std Dev = σ × √N
Annualized Information Ratio = (μ × N) / (σ × √N) = μ/σ × √N

# Formula 2: information_ratio = mean / std * np.sqrt(N)
information_ratio = μ/σ × √N

# They are completely equivalent!
```

### Why Write It as `mean / std * np.sqrt(N)` in Code?

This is a **more concise version** that directly multiplies daily data by the annualization factor, avoiding the intermediate steps of calculating annualized return and annualized standard deviation.

### Equivalence Verification

```python
import numpy as np

# Assume daily data
mu = 0.001      # Daily average excess return
sigma = 0.02    # Daily excess return std dev
N = 238         # Trading days per year

# Method 1: Annualize first, then divide
annual_return = mu * N                    # 0.001 × 238 = 0.238
annual_std = sigma * np.sqrt(N)           # 0.02 × 15.43 = 0.3086
ir1 = annual_return / annual_std          # 0.238 / 0.3086 = 0.771

# Method 2: Direct multiplication by √N
ir2 = mu / sigma * np.sqrt(N)             # 0.001/0.02 × 15.43 = 0.05 × 15.43 = 0.771

# They are exactly equal!
print(ir1 == ir2)  # True
```

### Why Use the Concise Version?

```python
# Concise version (used in code)
information_ratio = mean / std * np.sqrt(N)

# Expanded version (easier to understand)
annual_return = mean * N
annual_std = std * np.sqrt(N)
information_ratio = annual_return / annual_std

# Both are mathematically equivalent, but the concise version:
# - Has shorter code
# - Reduces intermediate variables
# - Is more computationally efficient
```

### Summary

| Version | Formula | Advantage |
|---------|---------|-----------|
| **Concise** | μ/σ × √N | Clean code, one-step calculation |
| **Expanded** | (μ×N) / (σ×√N) | Easier to understand the annualization process |

Your observation is very sharp! These two formulas are indeed different representations of the same mathematical expression.

## `sum` vs `product` Mode Selection Guide

**Source file**: [qlib/contrib/evaluate.py#L66](https://github.com/microsoft/qlib/blob/main/qlib/contrib/evaluate.py#L66)

### One-Sentence Rule

| Mode | Application Scenario | Mathematical Nature |
|------|---------------------|---------------------|
| **`sum`** | Short-term analysis, traditional finance, simple accumulation | Arithmetic returns |
| **`product`** | Long-term analysis, compound interest calculation, real investment | Geometric returns (log returns) |

### Detailed Comparison

#### 1. `sum` Mode (Arithmetic Returns)

```python
# Applicable Scenarios:
# - Daily or high-frequency trading
# - Short-term analysis (days to weeks)
# - Traditional financial reporting
# - Simple comparison with benchmarks

# Characteristics:
# - Simple and intuitive calculation
# - Assumes returns are linearly additive
# - Ignores compound interest effects
# - Adequate for short-term approximations
```

#### 2. `product` Mode (Geometric Returns)

```python
# Applicable Scenarios:
# - Long-term investment analysis (months/years)
# - Compound interest calculations
# - Realistic return assessment
# - Multi-period return accumulation

# Characteristics:
# - Considers compound interest effects
# - Returns are multiplied over time
# - More aligned with real-world investing
# - More accurate for long-term analysis
```

### Practical Examples

#### Short-term Analysis (Few Days)

```python
import numpy as np

# 3-day returns
r = [0.01, -0.02, 0.015]  # 1%, -2%, 1.5%

# `sum` mode
sum_return = np.sum(r)  # 0.005 (0.5%)
# Simple addition, acceptable for short-term approximation

# `product` mode
product_return = np.prod(1 + np.array(r)) - 1  # 0.0047 (0.47%)
# Considers compounding, more precise
```

#### Long-term Analysis (One Year)

```python
# One year of daily returns (simplified example)
r = [0.001] * 252  # 0.1% daily gain

# `sum` mode
annual_sum = np.sum(r)  # 0.252 (25.2%)
# Significantly overestimated!

# `product` mode
annual_product = np.prod(1 + np.array(r)) - 1  # 0.285 (28.5%)
# Considers compounding, more realistic
# (1.001)^252 - 1 ≈ 0.285
```

### Summary

| Factor | Use `sum` | Use `product` |
|--------|-----------|---------------|
| **Time Horizon** | Short-term | Long-term |
| **Compound Effect** | Ignored | Considered |
| **Calculation Complexity** | Simple | More complex |
| **Accuracy** | Approximate for short-term | Precise for long-term |
| **Typical Use Cases** | High-frequency trading, intraday | Portfolio analysis, fund evaluation |

## Understanding Log Returns in Qlib's Risk Analysis

**Source file**: [qlib/contrib/evaluate.py#L76](https://github.com/microsoft/qlib/blob/main/qlib/contrib/evaluate.py#L76)

This document explains the mathematical foundations and practical applications of log returns in financial risk analysis, specifically focusing on the calculation `std = np.log(1 + r).std(ddof=1)`.

---

## 1. The Core Formula: `std = np.log(1 + r).std(ddof=1)`

This line calculates the **standard deviation of log returns**, which is the standard method for measuring volatility in finance.

### Step-by-Step Calculation

#### Step 1: Convert Simple Returns to Log Returns

```python
r = [0.01, -0.02, 0.015, 0.005, -0.01]  # Simple returns

log_r = np.log(1 + r)
# Results:
# ln(1.01) = 0.00995
# ln(0.98) = -0.02020
# ln(1.015) = 0.01489
# ln(1.005) = 0.00499
# ln(0.99) = -0.01005
```

#### Step 2-5: Calculate Standard Deviation

```python
# Step 2: Calculate the mean
mean_log = log_r.mean()  # -0.000084

# Step 3: Calculate sum of squared deviations
deviations = log_r - mean_log
sum_sq = np.sum(deviations ** 2)  # 0.0008546

# Step 4: Calculate variance (ddof=1 for sample variance)
variance = sum_sq / (len(log_r) - 1)  # 0.00021365

# Step 5: Calculate standard deviation
std = np.sqrt(variance)  # 0.01462
```

#### Meaning of `ddof=1`

```python
# ddof = Delta Degrees of Freedom
# ddof=0: Population standard deviation (divide by n)
# ddof=1: Sample standard deviation (divide by n-1) - unbiased estimate
# In finance, we use historical data to estimate future risk, so we use sample std
```

---

## 2. Mathematical Derivation of `np.log(1 + r)`

### From Price to Log Return

```python
# Let:
P1 = Today's price
P0 = Yesterday's price

# Simple return r
r = (P1 - P0) / P0 = P1/P0 - 1

# Therefore:
1 + r = P1 / P0

# Take natural log of both sides
ln(1 + r) = ln(P1 / P0)

# Apply logarithm rule: ln(a/b) = ln(a) - ln(b)
ln(1 + r) = ln(P1) - ln(P0)
```

### Numerical Example

```python
import numpy as np

P1 = 105      # Today's price
P0 = 100      # Yesterday's price

r = (105 - 100) / 100 = 0.05  # 5%

# Verify equality
left = np.log(1 + r) = np.log(1.05) = 0.04879
right = np.log(105) - np.log(100) = 4.65396 - 4.60517 = 0.04879
assert left == right  # True
```

---

## 3. Mathematical Meaning of `ln(P1) - ln(P0)`

This expression represents the **continuously compounded return** or **log return**.

### Comparison of Return Types

| Return Type | Formula | Meaning |
|------------|---------|---------|
| **Absolute Change** | `P1 - P0` | Absolute price change |
| **Simple Return** | `(P1 - P0) / P0` | Percentage change (discrete compounding) |
| **Log Return** | `ln(P1) - ln(P0)` | Continuously compounded return |

### Numerical Comparison

```python
# Price increase: 100 → 105
simple_return = 5/100 = 0.05 = 5%
log_return = ln(105/100) = ln(1.05) = 0.04879 = 4.879%

# Price decrease: 100 → 95
simple_return = -5/100 = -0.05 = -5%
log_return = ln(95/100) = ln(0.95) = -0.05129 = -5.129%
```

---

## 4. Why Use Log Returns? (Complete Explanation)

### 4.1 Time Additivity

```python
# Simple returns are NOT additive
r1 = 0.10  # +10%
r2 = -0.10 # -10%
total_return = (1+0.10)*(1-0.10)-1 = -0.01  # -1% loss
# But r1 + r2 = 0, not equal to actual return

# Log returns ARE additive
log_r1 = ln(1.10) = 0.0953
log_r2 = ln(0.90) = -0.1054
sum_log = -0.0101
# Exactly equals ln(0.99) = -0.0101 (log of actual total return)

# Multi-period generalization
# Simple return (multiplicative): (1+r₁) × (1+r₂) × (1+r₃)
# Log return (additive): ln(1+r₁) + ln(1+r₂) + ln(1+r₃)
```

### 4.2 Symmetry

```python
# Simple returns are asymmetric
Up 10% then down 10%: 1.1 × 0.9 = 0.99 (1% loss)

# Log returns are symmetric
ln(1.1) + ln(0.9) = 0.09531 - 0.10536 = -0.01005
# Exactly equals ln(0.99)
```

### 4.3 Statistical Properties

```python
# Financial models (like Black-Scholes) assume prices follow a log-normal distribution
# This means log returns follow a normal distribution
# Normal distribution is easier to work with statistically
```

### 4.4 Geometric Interpretation

```python
# Log return = change on a logarithmic scale
# On a log-scale chart, the same percentage gain corresponds to the same vertical distance

# Example: +100% gain
Price: 10 → 20  (+100%)
Price: 100 → 200 (+100%)

# On a log scale:
ln(20)-ln(10) = ln(2) = 0.693
ln(200)-ln(100) = ln(2) = 0.693
# Both have the same vertical distance!
```

---

## 5. Application in Qlib's `product` Mode

```python
# In `product` mode, total return is multiplicative
total_return = (1+r₁) × (1+r₂) × ... × (1+rn)

# Taking logs converts multiplication to addition
ln(total_return) = ln(1+r₁) + ln(1+r₂) + ... + ln(1+rn)

# Therefore, the standard deviation of log returns can be used directly for risk assessment
# This is why `product` mode uses np.log(1 + r).std(ddof=1)
```

---

## Summary Table

| Aspect | Simple Return (`r`) | Log Return (`ln(1+r)`) |
|--------|---------------------|------------------------|
| **Time additivity** | ❌ No | ✅ Yes |
| **Symmetry** | ❌ No | ✅ Yes |
| **Normal distribution** | ❌ No (bounded) | ✅ Yes (unbounded) |
| **Multi-period calculation** | Multiplicative | Additive |
| **Range** | [-1, ∞) | (-∞, ∞) |
| **Financial interpretation** | Discrete compounding | Continuous compounding |

## Understanding `annualized_return = (1 + cumulative_return) ** (N / len(r)) - 1`

**Source file**: [qlib/contrib/evaluate.py#L79](https://github.com/microsoft/qlib/blob/main/qlib/contrib/evaluate.py#L79)

This formula calculates the **annualized return**, converting a total return over any time period into a standardized yearly return.

### 1. Basic Concepts

```python
# Variables from the code:
cumulative_return = Total return over the entire period (from start to end)
len(r) = Number of periods in the return series (e.g., trading days)
N = Annualization factor (e.g., 252 trading days in a year, 12 months in a year)

# Goal:
annualized_return = Annualized return (assuming yearly compounding)
```

### 2. Mathematical Derivation

#### Step 1: From Total Return to Final Value

```python
# Starting with 1 unit of capital
initial_value = 1

# Final value after len(r) periods
final_value = 1 + cumulative_return
```

#### Step 2: Define the Annualized Return

Let `R` be the annualized return (what we call `annualized_return`). If returns are compounded annually, the value after `len(r)/N` years is:

```python
final_value = (1 + R) ^ (len(r) / N)
```

#### Step 3: Establish the Equation

```python
(1 + R) ^ (len(r) / N) = 1 + cumulative_return
```

#### Step 4: Solve for R

```python
(1 + R) ^ (len(r) / N) = 1 + cumulative_return

# Take the (len(r)/N)-th root of both sides
1 + R = (1 + cumulative_return) ^ (1 / (len(r) / N))
1 + R = (1 + cumulative_return) ^ (N / len(r))

# Isolate R
R = (1 + cumulative_return) ^ (N / len(r)) - 1

# This is exactly:
annualized_return = (1 + cumulative_return) ** (N / len(r)) - 1
```

### 3. Numerical Examples

#### Example 1: Monthly Data Annualization

```python
# 3 months of returns
r = [0.01, 0.02, 0.015]  # 1%, 2%, 1.5%
len(r) = 3  # 3 months

# Calculate cumulative_return
cumulative_return = (1.01 * 1.02 * 1.015) - 1 = 0.0457 (4.57%)

# Annualization factor for monthly data
N = 12  # 12 months in a year

annualized_return = (1 + 0.0457) ** (12/3) - 1
                  = 1.0457 ** 4 - 1
                  = 1.195 - 1
                  = 0.195 (19.5%)
```

#### Example 2: Daily Data Annualization

```python
# 60 days of returns
# cumulative_return = (1+r₁)*(1+r₂)*...*(1+r₆₀) - 1
# Assume cumulative_return = 0.10 (10%)

len(r) = 60  # 60 trading days
N = 252  # 252 trading days in a year (for Chinese market)

annualized_return = (1 + 0.10) ** (252/60) - 1
                  = 1.10 ** 4.2 - 1
                  = 1.48 - 1
                  = 0.48 (48%)
```

### 4. Comparison with Simple Annualization

```python
# Simple (linear) annualization - INCORRECT for compounding returns
simple_annual = cumulative_return * (N / len(r))

# Compound (correct) annualization - what Qlib uses
compound_annual = (1 + cumulative_return) ** (N / len(r)) - 1

# Example comparison
cumulative_return = 0.10
len(r) = 60
N = 252

simple_annual = 0.10 * (252/60) = 0.10 * 4.2 = 0.42 (42%)
compound_annual = (1.10) ** (252/60) - 1 = 1.10 ** 4.2 - 1 = 1.48 - 1 = 0.48 (48%)
# Compound annualization is higher because it accounts for the compounding effect
```

### Summary Table

| Variable | Meaning | Example Value |
|----------|---------|---------------|
| `cumulative_return` | Total return over the entire period | 0.10 (10%) |
| `len(r)` | Number of periods in the return series | 60 days |
| `N` | Annualization factor (periods per year) | 252 (trading days) |
| `N / len(r)` | Annualization multiplier | 4.2 |
| `(1 + cumulative_return) ** (N/len(r))` | Scaled final value after one year | 1.48 |
| `annualized_return` | Final annualized return | 0.48 (48%) |

## Return Value Structure of `risk_analysis`

**Source file**: [qlib/contrib/evaluate.py#L94](https://github.com/microsoft/qlib/blob/main/qlib/contrib/evaluate.py#L94)

### Usage in `PortAnaRecord._generate`

```python
analysis = dict()
analysis["excess_return_without_cost"] = risk_analysis(
    report_normal["return"] - report_normal["bench"], 
    freq=_analysis_freq
)
```

### Return Value Example

Assuming daily return series input with `mode="product"`:

```python
import pandas as pd
import numpy as np

# Example daily return data
r = pd.Series([0.01, -0.02, 0.015, 0.005, -0.01])

# Function call
result = risk_analysis(r, freq="day", mode="product")

print(result)
```

**Output which equals Structure of `analysis["excess_return_without_cost"]`**:

```
                 risk
mean          -0.0001
std            0.0146
annualized_return -0.0245
information_ratio -0.2535
max_drawdown   -0.0202
```
