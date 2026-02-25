## Factor and Adjusted Price – Why Multiply? Divide?

https://github.com/microsoft/qlib/blob/main/qlib/backtest/exchange.py

### Basic Idea

This document explains a common confusion in Qlib:

- **Price** in backtest logic uses **`raw_price × factor`**  
- **Amount** in backtest logic uses **`amount ÷ factor`**

---

### Example: Stock Split

| Time         | Raw Price | Factor | Adjusted Price (stored in Qlib) |
|--------------|-----------|--------|----------------------------------|
| Before Split | 10        | 1.0    | 10 × 1.0 = 10                    |
| After Split  | 5         | 2.0    | 5 × 2.0 = 10                     |

---

### Code Example

```python
# In backtest, the price you see is ALWAYS adjusted
adjusted_price = raw_price * factor

# When you specify an order amount (e.g., buy 100 shares), 
# Qlib internally converts it to raw shares
raw_shares = order_amount / factor
```

---

## Volume Limits and Adjusted Price in Real-World Execution

### 1. `vol_limit` and `vol_limit[1]`

**Reference**: [`exchange.py#L329`](https://github.com/microsoft/qlib/blob/main/qlib/backtest/exchange.py#L329)

In `_get_vol_limit`, each volume limit is stored as a **2‑element tuple**.

#### Example 1 – Single Limit (applies to both buy & sell)

```python
volume_threshold = ("current", "$askV1")

# After processing:
vol_limit = ("current", "$askV1")
vol_limit[0] = "current"      # Type: real‑time or cumulative
vol_limit[1] = "$askV1"        # Field expression to query
```

#### Example 2 – Dictionary Form (Recommended)

```python
volume_threshold = {
    "buy": ("current", "$askV1"),
    "sell": ("current", "$bidV1"),
    "all": ("cum", "0.05 * $volume")
}
```

During iteration:

- `key="buy"`  → `vol_limit = ("current", "$askV1")` → `vol_limit[1] = "$askV1"`
- `key="sell"` → `vol_limit = ("current", "$bidV1")` → `vol_limit[1] = "$bidV1"`
- `key="all"`  → `vol_limit = ("cum",   "0.05 * $volume")` → `vol_limit[1] = "0.05 * $volume"`

#### Why `fields.add(vol_limit[1])`?

```python
fields.add(vol_limit[1])
```

This collects **every field expression** used in any volume limit into a set called `fields`.  
The final set might look like:

```python
{"$askV1", "$bidV1", "0.05 * $volume", "DayCumsum($volume)"}
```

These are added to `self.all_fields` and later passed to `D.features()`, guaranteeing that all necessary high‑frequency fields (e.g. Level‑2 order book data) are fetched in a single query.

#### Summary Table

| `vol_limit` example                     | `vol_limit[0]` | `vol_limit[1]`            | Type       | Typical Use Case               |
|-----------------------------------------|----------------|----------------------------|------------|---------------------------------|
| `("current", "$askV1")`                 | `current`      | `$askV1`                   | Real‑time  | Limit buy volume                |
| `("current", "$bidV1")`                 | `current`      | `$bidV1`                   | Real‑time  | Limit sell volume               |
| `("cum", "0.1 * $volume")`              | `cum`          | `0.1 * $volume`            | Cumulative | Daily volume cap                |
| `("cum", "DayCumsum($volume)")`         | `cum`          | `DayCsum($volume)`         | Cumulative | Intraday cumulative cap         |

**In short, `vol_limit[1]` is just a Qlib field‑expression string** that tells the system which data column to read when enforcing a volume limit.

---

### 2. `_update_limit` – Three Modes of Price Limits

**Reference**: [`exchange.py#L273`](https://github.com/microsoft/qlib/blob/main/qlib/backtest/exchange.py#L273)

Assume the original `self.quote_df` contains:

| instrument | datetime   | $close | $change | suspended |
|------------|------------|--------|---------|-----------|
| SH600000   | 2023-01-03 | 10.50  |  0.05   | False     |
| SH600000   | 2023-01-04 | 11.55  |  0.10   | False     |
| SH600000   | 2023-01-05 | 10.40  | -0.10   | False     |
| SH600000   | 2023-01-06 | NaN    |  NaN    | True      |
| SH600519   | 2023-01-04 | 1820   |  0.099  | False     |

#### Branch 1: No Limit (`limit_threshold=None` → `LT_NONE`)

```python
self.quote_df["limit_buy"]  = suspended
self.quote_df["limit_sell"] = suspended
```

| datetime   | limit_buy | limit_sell | Explanation                     |
|------------|-----------|------------|---------------------------------|
| 2023-01-03 | False     | False      | Normal trading                  |
| 2023-01-04 | False     | False      | Can buy even on limit‑up (US)   |
| 2023-01-05 | False     | False      | Can sell even on limit‑down (US)|
| 2023-01-06 | True      | True       | Suspended → cannot trade        |

**Suitable for**: US stocks, crypto, or any market without price limits.

#### Branch 2: Custom Expression Limit (`LT_TP_EXP`)

```python
limit_threshold = ("$change >= 0.095", "$change <= -0.095")   # ±9.5% rule

self.quote_df["limit_buy"]  = self.quote_df["$change >= 0.095"].astype(bool) | suspended
self.quote_df["limit_sell"] = self.quote_df["$change <= -0.095"].astype(bool) | suspended
```

| datetime   | $change >= 0.095 | $change <= -0.095 | limit_buy | limit_sell | Explanation                  |
|------------|------------------|-------------------|-----------|------------|------------------------------|
| 2023-01-03 | False            | False             | False     | False      | Normal                       |
| 2023-01-04 | True  (+10%)     | False             | True      | False      | ≥9.5% → cannot buy           |
| 2023-01-05 | False            | True   (-10%)     | False     | True       | ≤-9.5% → cannot sell         |
| 2023-01-06 | NaN              | NaN               | True      | True       | Suspended takes priority     |

**Suitable for**: Markets with custom or asymmetric rules (e.g. different limits for buy/sell).

#### Branch 3: Fixed Percentage Limit (`LT_FLT`) – Most Common, A‑Shares

```python
limit_threshold = 0.1    # 10%

self.quote_df["limit_buy"]  = self.quote_df["$change"].ge(0.1) | suspended
self.quote_df["limit_sell"] = self.quote_df["$change"].le(-0.1) | suspended
```

| datetime   | $change.ge(0.1) | $change.le(-0.1) | limit_buy | limit_sell | Explanation                  |
|------------|-----------------|------------------|-----------|------------|------------------------------|
| 2023-01-03 | False           | False            | False     | False      | Normal                       |
| 2023-01-04 | True  (+10%)    | False            | True      | False      | Limit‑up → cannot buy        |
| 2023-01-05 | False           | True   (-10%)    | False     | True       | Limit‑down → cannot sell     |
| 2023-01-06 | NaN             | NaN              | True      | True       | Suspended → cannot trade     |

**Suitable for**: China A‑share main board (±10%), STAR/ChiNext (±20%), etc.

---

### 3. Final Comparison (Same Day Behavior Across Modes)

| Date       | $change | Suspended | `LT_NONE` (US)        | `LT_TP_EXP` (Custom ±9.5%) | `LT_FLT` (A‑share ±10%) |
|------------|---------|-----------|------------------------|-----------------------------|-------------------------|
| 2023-01-04 | +10%    | No        | Can buy & sell         | **Cannot buy**              | **Cannot buy**         |
| 2023-01-05 | -10%    | No        | Can buy & sell         | **Cannot sell**             | **Cannot sell**        |
| 2023-01-06 | NaN     | Yes       | **Cannot trade**       | **Cannot trade**            | **Cannot trade**       |

### Summary

| Mode          | Key Parameter           | Behavior                                | Typical Market                 |
|---------------|-------------------------|-----------------------------------------|--------------------------------|
| `LT_NONE`     | `limit_threshold=None`  | No price limits, only suspension       | US stocks, crypto              |
| `LT_TP_EXP`   | `(expr_buy, expr_sell)` | Fully customizable via expressions     | Complex/custom rules           |
| `LT_FLT`      | `limit_threshold=0.1`   | Symmetric percentage limit (up & down) | China A‑share main board       |
