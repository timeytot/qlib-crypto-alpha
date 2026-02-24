# Information ration

https://github.com/microsoft/qlib/blob/main/qlib/contrib/evaluate.py#L85

Yes, these two formulas are **mathematically identical**!

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

This is a **more concise写法** that directly multiplies daily data by the annualization factor, avoiding the intermediate steps of calculating annualized return and annualized standard deviation.

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
