## Understanding Qlib's Exchange Module: Volume Limits and Order Execution

https://github.com/microsoft/qlib/blob/main/qlib/backtest/exchange.py

This document explains three interconnected aspects of Qlib's backtest exchange mechanism: volume limits, trading suspension handling, and the adjusted vs. real data architecture.

---

## 1. Volume Limits: `vol_limit` and `vol_limit[1]`

The `vol_limit` parameter controls trading volume caps. Let's examine its structure and usage.

### Code Reference
- [`exchange.py#L329`](https://github.com/microsoft/qlib/blob/main/qlib/backtest/exchange.py#L329): `fields.add(vol_limit[1])`

### What is `vol_limit`?

`vol_limit` is a 2-element tuple retrieved from the `_get_vol_limit` method. Its structure depends on how you configure `volume_threshold`.

#### Example 1: Single Limit (Tuple Form)
```python
volume_threshold = ("current", "$askV1")

# After processing:
vol_limit = ("current", "$askV1")
vol_limit[0] = "current"  # Limit type
vol_limit[1] = "$askV1"   # Field expression
```

#### Example 2: Dictionary Form (Buy/Sell Separation) – Recommended
```python
volume_threshold = {
    "buy": ("current", "$askV1"),    # Buy limit uses ask price
    "sell": ("current", "$bidV1"),   # Sell limit uses bid price
    "all": ("cum", "0.05 * $volume") # Overall cumulative cap
}

# During iteration:
# First: key="buy"  → vol_limit = ("current", "$askV1") → vol_limit[1] = "$askV1"
# Second: key="sell" → vol_limit = ("current", "$bidV1") → vol_limit[1] = "$bidV1"
# Third: key="all"  → vol_limit = ("cum", "0.05 * $volume") → vol_limit[1] = "0.05 * $volume"
```

### Purpose of `fields.add(vol_limit[1])`

```python
fields.add(vol_limit[1])
```

This collects all field expressions from volume limits into a set. The final `fields` might look like:
```python
{"$askV1", "$bidV1", "0.05 * $volume"}
```

These fields are added to `self.all_fields` and queried together in `D.features()`, ensuring the dataset includes necessary high-frequency fields (e.g., Level-2 order book data).

### Summary Table: Volume Limit Types

| `vol_limit` Example                     | `vol_limit[0]` | `vol_limit[1]`            | Type       | Typical Use Case               |
|-----------------------------------------|----------------|----------------------------|------------|---------------------------------|
| `("current", "$askV1")`                 | `"current"`    | `"$askV1"`                 | Real‑time  | Limit buy volume                |
| `("current", "$bidV1")`                 | `"current"`    | `"$bidV1"`                 | Real‑time  | Limit sell volume               |
| `("cum", "0.1 * $volume")`              | `"cum"`        | `"0.1 * $volume"`          | Cumulative | Daily volume cap                |
| `("cum", "DayCumsum($volume)")`         | `"cum"`        | `"DayCumsum($volume)"`     | Cumulative | Intraday cumulative cap         |

Thus, `vol_limit[1]` is simply a Qlib field expression string that tells the system which field to query for calculating the volume cap.

---

## 2. Trading Suspension and Limit Handling

The `_update_limit()` method ([`exchange.py#L273`](https://github.com/microsoft/qlib/blob/main/qlib/backtest/exchange.py#L273)) controls when trading is allowed based on price limits and suspensions.

### Sample Data

Assume `self.quote_df` contains:

| instrument | datetime   | $close | $change | suspended |
|------------|------------|--------|---------|-----------|
| SH600000   | 2023-01-03 | 10.50  | 0.05    | False     |
| SH600000   | 2023-01-04 | 11.55  | 0.10    | False     |
| SH600000   | 2023-01-05 | 10.40  | -0.10   | False     |
| SH600000   | 2023-01-06 | NaN    | NaN     | True      |
| SH600519   | 2023-01-04 | 1820.0 | 0.099   | False     |

### Branch 1: No Limit (`limit_threshold=None` → `LT_NONE`)

```python
self.quote_df["limit_buy"] = suspended
self.quote_df["limit_sell"] = suspended
```

| datetime   | limit_buy | limit_sell | Explanation                     |
|------------|-----------|------------|---------------------------------|
| 2023-01-03 | False     | False      | Normal trading                  |
| 2023-01-04 | False     | False      | Can buy even on limit-up (US stocks) |
| 2023-01-05 | False     | False      | Can sell even on limit-down (US stocks) |
| 2023-01-06 | True      | True       | Suspended → cannot trade        |

→ Only suspension restricts trading; price limits have no effect.

### Branch 2: Custom Expression Limit (`LT_TP_EXP`)

User setting:
```python
limit_threshold = ("$change >= 0.095", "$change <= -0.095")  # Custom ±9.5% rule
```

Executed code:
```python
self.quote_df["limit_buy"]  = self.quote_df["$change >= 0.095"].astype(bool) | suspended
self.quote_df["limit_sell"] = self.quote_df["$change <= -0.095"].astype(bool) | suspended
```

| datetime   | $change ≥ 0.095 | $change ≤ -0.095 | limit_buy | limit_sell | Explanation                  |
|------------|-----------------|------------------|-----------|------------|------------------------------|
| 2023-01-03 | False           | False            | False     | False      | Normal                       |
| 2023-01-04 | True  (+10%)    | False            | True      | False      | ≥9.5% → cannot buy           |
| 2023-01-05 | False           | True   (-10%)    | False     | True       | ≤-9.5% → cannot sell         |
| 2023-01-06 | NaN             | NaN              | True      | True       | Suspended takes priority     |

→ Highly flexible — can implement special rules like ±5% for ST stocks or ±20% for STAR Market.

### Branch 3: Fixed Percentage Limit (`LT_FLT`) – Most Common (A-Shares)

User setting:
```python
limit_threshold = 0.1  # 10%
```

Executed code:
```python
self.quote_df["limit_buy"]  = self.quote_df["$change"].ge(0.1) | suspended
self.quote_df["limit_sell"] = self.quote_df["$change"].le(-0.1) | suspended
```

| datetime   | $change ≥ 0.1 | $change ≤ -0.1 | limit_buy | limit_sell | Explanation                  |
|------------|---------------|----------------|-----------|------------|------------------------------|
| 2023-01-03 | False         | False          | False     | False      | Normal trading               |
| 2023-01-04 | True  (+10%)  | False          | True      | False      | Limit-up → cannot buy        |
| 2023-01-05 | False         | True   (-10%)  | False     | True       | Limit-down → cannot sell     |
| 2023-01-06 | NaN           | NaN            | True      | True       | Suspended → cannot trade     |

→ Perfectly simulates the ±10% daily limit rule on China's main board.

### Comparison Table (Same Day Across Modes)

| Date       | $change | Suspended | `LT_NONE` (US-style) | `LT_TP_EXP` (Custom ±9.5%) | `LT_FLT` (A-share ±10%) |
|------------|---------|-----------|----------------------|-----------------------------|-------------------------|
| 2023-01-04 | +10%    | No        | Can buy & sell       | Cannot buy                  | Cannot buy              |
| 2023-01-05 | -10%    | No        | Can buy & sell       | Cannot sell                 | Cannot sell             |
| 2023-01-06 | NaN     | Yes       | Cannot trade         | Cannot trade                | Cannot trade            |

**Summary:**
- **`LT_NONE`**: Most permissive → ideal for US stocks or crypto
- **`LT_TP_EXP`**: Most flexible → for complex or custom rules
- **`LT_FLT`**: Standard and recommended → perfectly matches China's A-share main board limits

---

## 3. Adjusted vs. Normal Data: Qlib's Core Pattern

This section ([`exchange.py#L783`](https://github.com/microsoft/qlib/blob/main/qlib/backtest/exchange.py#L783)) explains how Qlib handles the separation between **internal adjusted data** and **real-world execution**.

### The Core Idea: Two Layers of Reality

Qlib operates on two distinct layers to bridge clean strategy design with messy real-world trading:

#### Strategy Logic Layer (Adjusted World)
- **Purpose**: Where your strategy lives, makes decisions, and generates signals
- **Data Type**: Uses **adjusted prices** and **adjusted quantities**
- **Key Property**: **Continuity** — artificially removes discontinuities from stock splits and dividends
- **Benefit**: Strategy responds only to genuine market movements, not accounting artifacts

#### Order Execution Layer (Real World)
- **Purpose**: Simulates or submits orders that comply with real exchange rules
- **Data Type**: Uses **real market prices** and **real trading lot sizes** (e.g., 100-share "boards" in A-shares)
- **Key Property**: **Precision & Compliance** — respects exchange prices and minimum tradable units

**The crucial link**: When your strategy decides to trade, its intention (e.g., "buy 100 adjusted shares") must be translated from the **adjusted world** to the **real world**. Functions like `round_amount_by_trade_unit` handle this translation.

### How Translation Works: A Step-by-Step Example (Partial Fill)

Let's trace "buy 75 adjusted shares" after a 2-for-1 stock split:

#### Pre-Split State:
- **Real World**: Price: $100/share, Minimum Lot Size: 100 shares
- **Adjusted World**: Price: $100/share, Factor: 1.0
- **Meaning**: 1 "adjusted share" = 1 real share

#### After 2-for-1 Split:
- **Real World**: Price: $50/share, 1 original share = 2 new shares, Lot size: 100 shares
- **Adjusted World**: Price: $100/share (for continuity), Factor: 2.0
- **Meaning**: 1 "adjusted share" = 2 real shares

#### Strategy Action:
Model signals: "Buy 75 adjusted shares" (economic exposure equivalent to 75 pre-split shares)

#### Execution Process (`round_amount_by_trade_unit`):

1. **Convert to Real Share Demand**:
   ```
   75 adjusted shares × 2.0 (factor) = 150 real shares
   ```

2. **Apply Trading Rules (The // Step – Enforcing Lot Size)**:
   ```
   Tradable Lots = 150 real shares // 100 shares per lot
   Tradable Lots = 1 (remainder of 50 shares discarded as invalid partial lot)
   ```
   Result: System executes 1 full lot = **100 real shares**

   👉 The `//` operator causes a **partial fill** — 50 real shares (33% of original demand) are unexecutable.

3. **Convert Back for Strategy Consistency**:
   ```
   100 real shares ÷ 2.0 (factor) = 50 adjusted shares
   ```
   Strategy is informed that only 50 of its requested 75 adjusted shares were filled.

### Why This Design is Essential

This two-layer architecture solves a critical problem: **isolating strategy logic from market noise**.

- **For Strategy Developers**: Design and test logic in a **pure, continuous environment** without constantly handling splits or dividends
- **For Backtest Realism**: System automatically applies **real-world trading friction** (lot size restrictions) when simulating orders

In essence, Qlib acts as a **perfect translator**. Your strategy speaks the language of "continuous adjusted data." Qlib translates that intent into "compliant real-world orders," executes them, and reports results back in the language your strategy understands.

---

## 4. Factor and Adjusted Price – Why Multiply? Divide?

### Basic Idea

This explains a common confusion in Qlib:

- **Price** in backtest logic uses **`raw_price × factor`**  
- **Amount** in backtest logic uses **`amount ÷ factor`**

### Example: Stock Split

| Time         | Raw Price | Factor | Adjusted Price (stored in Qlib) |
|--------------|-----------|--------|----------------------------------|
| Before Split | 10        | 1.0    | 10 × 1.0 = 10                    |
| After Split  | 5         | 2.0    | 5 × 2.0 = 10                     |

### Code Example

```python
# In backtest, the price you see is ALWAYS adjusted
adjusted_price = raw_price * factor

# When you specify an order amount (e.g., buy 100 shares), 
# Qlib internally converts it to raw shares
raw_shares = order_amount / factor
```

---

## Important Note on Cryptocurrencies

This pattern with `factor` and `trade_unit` is most critical for **traditional equity markets** (like A-shares) where corporate actions and lot size rules are strict. For **cryptocurrency** trading, where assets don't split in the same way and fractional units are standard, this logic is often unnecessary and can be greatly simplified or removed.
