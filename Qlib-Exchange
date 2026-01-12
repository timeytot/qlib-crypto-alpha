https://github.com/microsoft/qlib/blob/main/qlib/backtest/exchange.py#L329  fields.add(vol_limit[1])

  What do vol_limit and vol_limit[1] look like?In the _get_vol_limit method, vol_limit is simply one of these 2-element tuples.Example 1: Single limitpython
  
  volume_threshold = ("current", "$askV1")
  
  After processing:vol_limit = ("current", "$askV1")
  vol_limit[0] = "current"
  vol_limit[1] = "$askV1"
  
  Example 2: Dictionary form (recommended)python
  
  volume_threshold = {
      "buy": ("current", "$askV1"),
      "sell": ("current", "$bidV1"),
      "all": ("cum", "0.05 * $volume")
  }
  
  During iteration:First: key="buy" → vol_limit = ("current", "$askV1") → vol_limit[1] = "$askV1"
  Second: key="sell" → vol_limit = ("current", "$bidV1") → vol_limit[1] = "$bidV1"
  Third: key="all" → vol_limit = ("cum", "0.05 * $volume") → vol_limit[1] = "0.05 * $volume"
  
  Purpose of fields.add(vol_limit[1])python
  
  fields.add(vol_limit[1])
  
  This collects all field expressions used in the limits into a fields set.The final fields might look like:python
  
  {"$askV1", "$bidV1", "0.05 * $volume"}
  
  These are then added to self.all_fields and queried together in D.features(), ensuring the dataset includes the necessary high-frequency fields (e.g., Level-2 order book data).Summary tablevol_limit example
  vol_limit[0]
  vol_limit[1]
  Type
  Typical use case
  ("current", "$askV1")
  "current"
  "$askV1"
  Real-time
  Limit buy volume
  ("current", "$bidV1")
  "current"
  "$bidV1"
  Real-time
  Limit sell volume
  ("cum", "0.1 * $volume")
  "cum"
  "0.1 * $volume"
  Cumulative
  Daily volume cap
  ("cum", "DayCumsum($volume)")
  "cum"
  "DayCumsum($volume)"
  Cumulative
  Intraday cumulative cap
  
  Thus, vol_limit[1] is simply a Qlib field expression string that tells the system which field to query for calculating the volume cap.

https://github.com/microsoft/qlib/blob/main/qlib/backtest/exchange.py#L273  _update_limit

  Data Examples for the Three Branches in _update_limit()Assume the original self.quote_df contains the following key columns (simplified):
  instrument	datetime	$close	$change (return)	suspended (paused)
  SH600000	2023-01-03	10.50	0.05 (+5%)	False
  SH600000	2023-01-04	11.55	0.10 (+10%)	False
  SH600000	2023-01-05	10.40	-0.10 (-10%)	False
  SH600000	2023-01-06	NaN	NaN	True
  SH600519	2023-01-04	1820.0	0.099 (+9.9%)	False
  Branch 1: No Limit (limit_threshold=None → LT_NONE)Executed code:
  python
  self.quote_df["limit_buy"] = suspendedself.quote_df["limit_sell"] = suspended
  Result:
  datetime	limit_buy	limit_sell	Explanation
  2023-01-03	False	False	Normal trading
  2023-01-04	False	False	Can buy even on limit-up! (suitable for US stocks)
  2023-01-05	False	False	Can sell even on limit-down! (suitable for US stocks)
  2023-01-06	True	True	Paused → cannot trade
  → Only suspension restricts trading; limit-up/down has no effect.
  Branch 2: Custom Expression Limit (LT_TP_EXP)User setting:
  python
  limit_threshold = ("$change >= 0.095", "$change <= -0.095")  # Custom ±9.5% rule
  Executed code:
  python
  self.quote_df["limit_buy"]  = self.quote_df["$change >= 0.095"].astype(bool) | suspendedself.quote_df["limit_sell"] = self.quote_df["$change <= -0.095"].astype(bool) | suspended
  Result:
  datetime	$change >= 0.095	$change <= -0.095	limit_buy	limit_sell	Explanation
  2023-01-03	False	False	False	False	Normal
  2023-01-04	True (+10%)	False	True	False	≥9.5% → cannot buy
  2023-01-05	False	True (-10%)	False	True	≤-9.5% → cannot sell
  2023-01-06	NaN	NaN	True	True	Paused takes priority
  → Highly flexible — can implement special rules like ±5% for ST stocks or ±20% for STAR Market.
  Branch 3: Fixed Percentage Limit (LT_FLT) — Most Common, Suitable for A-SharesUser setting:
  python
  limit_threshold = 0.1  # 10%
  Executed code:
  python
  self.quote_df["limit_buy"]  = self.quote_df["$change"].ge(0.1) | suspendedself.quote_df["limit_sell"] = self.quote_df["$change"].le(-0.1) | suspended
  Result:
  datetime	$change.ge(0.1)	$change.le(-0.1)	limit_buy	limit_sell	Explanation
  2023-01-03	False	False	False	False	Normal trading
  2023-01-04	True (+10%)	False	True	False	Limit-up → cannot buy (real A-share rule)
  2023-01-05	False	True (-10%)	False	True	Limit-down → cannot sell (real A-share rule)
  2023-01-06	NaN	NaN	True	True	Paused → cannot trade
  → Perfectly simulates the ±10% daily limit rule on China's main board (default and most commonly used).Final Comparison Table (Same Day Behavior Across Modes)
  Date	$change	Paused	LT_NONE (US-style)	LT_TP_EXP (Custom ±9.5%)	LT_FLT (A-share ±10%)
  2023-01-04	+10%	No	Can buy & sell	Cannot buy	Cannot buy
  2023-01-05	-10%	No	Can buy & sell	Cannot sell	Cannot sell
  2023-01-06	NaN	Yes	Cannot trade	Cannot trade	Cannot trade
  Summary:
  LT_NONE: Most permissive → ideal for US stocks or crypto
  LT_TP_EXP: Most flexible → for complex or custom rules
  LT_FLT: Standard and recommended → perfectly matches China's A-share main board limits

https://github.com/microsoft/qlib/blob/main/qlib/backtest/exchange.py#L783  adjusted vs normal

  # Qlib's Core Pattern: Internal Adjusted Data vs. Real-World Execution
  
  This note explains a fundamental design pattern in **Qlib** regarding how trading quantities are handled. The system maintains a clear separation between **adjusted data** used for internal strategy logic and **real-world quantities** used for order execution.
  
  ## The Core Idea: Two Layers of Reality
  
  Qlib operates on two distinct layers to bridge the gap between clean strategy design and messy real-world trading:
  
  1.  **Strategy Logic Layer (Adjusted World)**
      *   **Purpose**: This is where your strategy lives, makes decisions, and generates signals.
      *   **Data Type**: It uses **adjusted prices** and **adjusted quantities**.
      *   **Key Property**: **Continuity**. This layer artificially removes all discontinuities caused by corporate actions like stock splits (e.g., a 2-for-1 split) or dividends. Prices and quantities are normalized over time, allowing a strategy's logic (like a moving average crossover) to respond only to genuine market movements, not accounting artifacts. The strategy always thinks in terms of this continuous, "clean" time series.
  
  2.  **Order Execution Layer (Real World)**
      *   **Purpose**: This layer simulates or submits actual orders that must comply with real exchange rules.
      *   **Data Type**: It uses **real market prices** and **real trading lot sizes** (e.g., 100-share "boards" in A-shares).
      *   **Key Property**: **Precision & Compliance**. It must respect the precise prices on an exchange and the minimum tradable unit.
  
  **The crucial link**: When your strategy decides to trade, it outputs an intention (e.g., "buy 100 adjusted shares"). Before this order can be simulated, it must be translated from the **adjusted world** into the **real world**. This is the job of functions like `round_amount_by_trade_unit`.
  
  How the Translation Works: A Step-by-Step Example (Illustrating Partial Fill)
  Let's trace what happens when your strategy wants to "buy 75 adjusted shares" after a 2-for-1 stock split. This example highlights how the integer division (//) for lot size can lead to a partial fill of the original order.
  
  Pre-Split State:
  
  Real World (Market): Price: $100/share. Minimum Lot Size: 100 shares.
  
  Adjusted World (Strategy View): Price: $100/share. Factor: 1.0.
  
  Meaning: 1 "adjusted share" equals 1 real share.
  
  After a 2-for-1 Split:
  
  Real World (Market): Price: $50/share. What was 1 real share becomes 2 real shares. Lot size rule remains: trade in multiples of 100 shares.
  
  Adjusted World (Strategy View): Price remains at $100/share for continuity.
  
  Factor is updated to 2.0 (1 "adjusted share" = 2 real shares).
  
  Strategy Action:
  Your model signals: "Buy 75 (adjusted) shares." This means: "Establish an economic exposure equivalent to 75 pre-split shares."
  
  Execution Process (round_amount_by_trade_unit):
  
  Convert to Real Share Demand:
  75 adjusted shares * 2.0 (factor) = 150 real shares
  (The strategy's intent translates to needing 150 of today's shares.)
  
  Apply Trading Rules (The // Step - Enforcing Lot Size):
  This is the critical step where integer division (//) enforces the "whole lots only" rule.
  
  Tradable Lots = 150 real shares // 100 shares per lot
  
  Tradable Lots = 1 (The integer quotient is 1. The remainder of 50 shares is discarded as it's an invalid partial lot).
  
  Result: The system can only execute 1 full lot, which equals 1 * 100 = **100 real shares**.
  
  👉 The // operator causes a partial fill. 50 real shares (33% of the original demand) are un-executable due to lot size constraints.
  
  Convert Back for Strategy Consistency:
  100 real shares / 2.0 (factor) = 50 adjusted shares
  (The strategy is informed that only 50 of its requested 75 adjusted shares were filled.)
  
  ## Why This Design is Essential
  
  This two-layer architecture solves a critical problem in backtesting: **isolating strategy logic from market noise**.
  
  *   **For the Strategy Developer**: You can design and test logic in a **pure, continuous environment**. You don't have to constantly write code to handle splits or dividends; Qlib's adjusted layer does it for you.
  *   **For Backtest Realism**: The system automatically applies **real-world trading friction** (like lot size restrictions) when simulating orders. This prevents a strategy from assuming it can buy odd lots of 50 shares if the market requires 100-share blocks.
  
  In essence, Qlib acts as a **perfect translator**. Your strategy speaks the language of "continuous adjusted data." Qlib listens, translates that intent into "compliant real-world orders," executes them, and then reports the results back in the language your strategy understands.
  
  ## Important Note on Cryptocurrencies
  
  This specific pattern with `factor` and `trade_unit` is most critical for **traditional equity markets** (like A-shares) where corporate actions and lot size rules are strict. For **cryptocurrency** trading, where assets don't split in the same way and fractional units are standard, this logic is often unnecessary and can be greatly simplified or removed.
