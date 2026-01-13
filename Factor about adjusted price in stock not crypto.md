# Factor and Adjusted Price

## Basic Idea

This document explains why:

- price uses `× factor`
- amount uses `÷ factor`

---

## Example

| Time | Raw Price | Adjusted Price |
|----|----|----|
| Before | 10 | 20 |
| After | 5 | 5 |

---

## Code Example

```python
adjusted_price = raw_price * factor
# Qlib: Vol Limit, Adjusted Price, and Real-World Execution

This document explains how **Qlib** handles volume limits, adjusted prices, and the translation between strategy logic and real-world execution.

```

## 1. vol_limit and vol_limit[1]

Reference: [exchange.py #L329](https://github.com/microsoft/qlib/blob/main/qlib/backtest/exchange.py#L329)

In the `_get_vol_limit` method, `vol_limit` is one of these 2-element tuples.

### Example 1: Single limit

```python
volume_threshold = ("current", "$askV1")

# After processing
vol_limit = ("current", "$askV1")
vol_limit[0] = "current"
vol_limit[1] = "$askV1"
Example 2: Dictionary form (recommended)
python
复制代码
volume_threshold = {
    "buy": ("current", "$askV1"),
    "sell": ("current", "$bidV1"),
    "all": ("cum", "0.05 * $volume")
}
During iteration:

key="buy" → vol_limit = ("current", "$askV1") → vol_limit[1] = "$askV1"

key="sell" → vol_limit = ("current", "$bidV1") → vol_limit[1] = "$bidV1"

key="all" → vol_limit = ("cum", "0.05 * $volume") → vol_limit[1] = "0.05 * $volume"

Purpose of fields.add(vol_limit[1])

python
复制代码
fields.add(vol_limit[1])
This collects all field expressions used in the limits into a fields set.
The final fields might look like:

python
复制代码
{"$askV1", "$bidV1", "0.05 * $volume"}
These are added to self.all_fields and queried together in D.features(), ensuring the dataset includes necessary high-frequency fields (e.g., Level-2 order book data).

Summary Table
vol_limit example	vol_limit[0]	vol_limit[1]	Type	Typical use case
("current", "$askV1")	current	$askV1	Real-time	Limit buy volume
("current", "$bidV1")	current	$bidV1	Real-time	Limit sell volume
("cum", "0.1 * $volume")	cum	0.1 * $volume	Cumulative	Daily volume cap
("cum", "DayCumsum($volume)")	cum	DayCumsum($volume)	Cumulative	Intraday cumulative cap

Thus, vol_limit[1] is simply a Qlib field expression string that tells the system which field to query for calculating the volume cap.

2. _update_limit Examples
Reference: exchange.py #L273

Assume the original self.quote_df contains:

instrument	datetime	$close	$change	suspended
SH600000	2023-01-03	10.50	0.05	False
SH600000	2023-01-04	11.55	0.10	False
SH600000	2023-01-05	10.40	-0.10	False
SH600000	2023-01-06	NaN	NaN	True
SH600519	2023-01-04	1820	0.099	False

Branch 1: No Limit (limit_threshold=None → LT_NONE)
python
复制代码
self.quote_df["limit_buy"] = suspended
self.quote_df["limit_sell"] = suspended
datetime	limit_buy	limit_sell	Explanation
2023-01-03	False	False	Normal trading
2023-01-04	False	False	Can buy even on limit-up (US stocks)
2023-01-05	False	False	Can sell even on limit-down (US stocks)
2023-01-06	True	True	Paused → cannot trade

Branch 2: Custom Expression Limit (LT_TP_EXP)
python
复制代码
limit_threshold = ("$change >= 0.095", "$change <= -0.095")  # Custom ±9.5% rule
self.quote_df["limit_buy"]  = self.quote_df["$change >= 0.095"].astype(bool) | suspended
self.quote_df["limit_sell"] = self.quote_df["$change <= -0.095"].astype(bool) | suspended
datetime	$change >= 0.095	$change <= -0.095	limit_buy	limit_sell	Explanation
2023-01-03	False	False	False	False	Normal
2023-01-04	True (+10%)	False	True	False	≥9.5% → cannot buy
2023-01-05	False	True (-10%)	False	True	≤-9.5% → cannot sell
2023-01-06	NaN	NaN	True	True	Paused takes priority

Branch 3: Fixed Percentage Limit (LT_FLT) — Most Common, Suitable for A-Shares
python
复制代码
limit_threshold = 0.1  # 10%
self.quote_df["limit_buy"]  = self.quote_df["$change"].ge(0.1) | suspended
self.quote_df["limit_sell"] = self.quote_df["$change"].le(-0.1) | suspended
datetime	$change.ge(0.1)	$change.le(-0.1)	limit_buy	limit_sell	Explanation
2023-01-03	False	False	False	False	Normal trading
2023-01-04	True (+10%)	False	True	False	Limit-up → cannot buy
2023-01-05	False	True (-10%)	False	True	Limit-down → cannot sell
2023-01-06	NaN	NaN	True	True	Paused → cannot trade

Final Comparison Table (Same Day Behavior Across Modes)
Date	$change	Paused	LT_NONE (US)	LT_TP_EXP (Custom ±9.5%)	LT_FLT (A-share ±10%)
2023-01-04	+10%	No	Can buy & sell	Cannot buy	Cannot buy
2023-01-05	-10%	No	Can buy & sell	Cannot sell	Cannot sell
2023-01-06	NaN	Yes	Cannot trade	Cannot trade	Cannot trade

Summary:

LT_NONE: Most permissive → ideal for US stocks or crypto

LT_TP_EXP: Most flexible → for complex/custom rules

LT_FLT: Standard → matches China's A-share main board limits
