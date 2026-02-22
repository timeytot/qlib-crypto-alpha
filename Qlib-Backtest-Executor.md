https://github.com/microsoft/qlib/blob/main/qlib/backtest/executor.py#L462
## Structure of `decision_list`

In a nested backtest scenario (outer level: daily, inner level: minute-level with 240 minutes per trading day in a standard A-share market), `decision_list` is a **list of tuples**, where each tuple records:

- the inner-level trade decision for that minute (`_inner_trade_decision`)
- the start and end timestamps of that minute (`*sub_cal.get_step_time()`)

This list is built incrementally inside `NestedExecutor._collect_data` via:

```python
decision_list.append((_inner_trade_decision, *sub_cal.get_step_time()))
```

### Purpose

`decision_list` is used together with `inner_order_indicators` in `_agg_base_price` to compute benchmark prices (TWAP/VWAP) for each stock across the day:

```python
for oi, (dec, start, end) in zip(inner_order_indicators, decision_list):
    bp_tmp, bv_tmp = self._get_base_vol_pri(
        inst, start, end, decision=dec, ...
    )
```

It provides the exact time window and decision context needed to query correct benchmark prices from the exchange.

### Example Structure (3-minute simplified day)

```python
decision_list = [
    # ========== Minute 1 (09:30–09:31) ==========
    (
        TradeDecisionWO(
            order_list=[
                Order(stock_id='SH600000', amount=100, direction=Order.BUY),
                Order(stock_id='SH600001', amount=200, direction=Order.BUY)
            ]
        ),
        pd.Timestamp('2026-02-20 09:30:00'),    # start_time
        pd.Timestamp('2026-02-20 09:31:00')     # end_time
    ),

    # ========== Minute 2 (09:31–09:32) ==========
    (
        TradeDecisionWO(
            order_list=[
                Order(stock_id='SH600000', amount=150, direction=Order.BUY),
                Order(stock_id='SH600002', amount=300, direction=Order.BUY)
            ]
        ),
        pd.Timestamp('2026-02-20 09:31:00'),
        pd.Timestamp('2026-02-20 09:32:00')
    ),

    # ========== Minute 3 (09:32–09:33) ==========
    (
        TradeDecisionWO(
            order_list=[
                Order(stock_id='SH600001', amount=250, direction=Order.BUY),
                Order(stock_id='SH600002', amount=200, direction=Order.BUY)
            ]
        ),
        pd.Timestamp('2026-02-20 09:32:00'),
        pd.Timestamp('2026-02-20 09:33:00')
    )
]
```

### In-Memory Representation (Simplified)

```
decision_list = [
    (<TradeDecisionWO object at 0x7f8a1c0a4a90>, Timestamp('2026-02-20 09:30:00'), Timestamp('2026-02-20 09:31:00')),
    (<TradeDecisionWO object at 0x7f8a1c0a4b50>, Timestamp('2026-02-20 09:31:00'), Timestamp('2026-02-20 09:32:00')),
    (<TradeDecisionWO object at 0x7f8a1c0a4c10>, Timestamp('2026-02-20 09:32:00'), Timestamp('2026-02-20 09:33:00'))
]
```

### Key Points

1. **Length**: `len(decision_list) = 240` (minutes in a trading day) in a full-day backtest
2. **Each element**: A 3-tuple containing:
   - `TradeDecisionWO` object (the minute-level trading decision)
   - `start_time` (when the minute began)
   - `end_time` (when the minute ended)
3. **One-to-one correspondence**: `decision_list[i]` corresponds to `inner_order_indicators[i]` — the i-th minute's decision and its resulting metrics
4. **Purpose**: Enables per-minute benchmark price calculation by providing the exact time window and decision context for each stock

### One-Sentence Summary

`decision_list` is a **time-stamped log of every inner-level trading decision**, perfectly aligned with `inner_order_indicators` to provide the temporal context needed for accurate benchmark price computation.

https://github.com/microsoft/qlib/blob/main/qlib/backtest/executor.py#L473
## Structure of `inner_order_indicators`

In a typical nested backtest scenario (outer level: daily, inner level: minute-level with 240 minutes per trading day), `inner_order_indicators` is ultimately **a list containing 240 `NumpyOrderIndicator` objects** — one for each minute of the trading day.

### Example Structure

```python
inner_order_indicators = [
    # ========== Minute 1 (09:30–09:31) ==========
    NumpyOrderIndicator({
        'deal_amount': SingleData({'SH600000': 100, 'SH600001': 200}),      # actual dealt volume
        'trade_value': SingleData({'SH600000': 1050, 'SH600001': 4060}),    # trade value (temporary, will be adjusted)
        'trade_price': SingleData({'SH600000': 1050, 'SH600001': 4060}),    # temporary (later converted to average price)
        'inner_amount': SingleData({'SH600000': 100, 'SH600001': 200}),     # inner-level target amount
        'trade_dir': SingleData({'SH600000': 1, 'SH600001': 1}),           # direction (1 = BUY, 0 = SELL)
        # ... other fields (ffr, pa, etc.)
    }),

    # ========== Minute 2 (09:31–09:32) ==========
    NumpyOrderIndicator({
        'deal_amount': SingleData({'SH600000': 150, 'SH600002': 300}),
        'trade_value': SingleData({'SH600000': 1620, 'SH600002': 4500}),
        'trade_price': SingleData({'SH600000': 1620, 'SH600002': 4500}),
        'inner_amount': SingleData({'SH600000': 150, 'SH600002': 300}),
        'trade_dir': SingleData({'SH600000': 1, 'SH600002': 1}),
        # ...
    }),

    # ========== Minute 3 (09:32–09:33) ==========
    NumpyOrderIndicator({
        'deal_amount': SingleData({'SH600001': 250, 'SH600002': 200}),
        'trade_value': SingleData({'SH600001': 5075, 'SH600002': 3000}),
        'trade_price': SingleData({'SH600001': 5075, 'SH600002': 3000}),
        'inner_amount': SingleData({'SH600001': 250, 'SH600002': 200}),
        'trade_dir': SingleData({'SH600001': 1, 'SH600002': 1}),
        # ...
    }),

    # ... minutes 4 to 239 ...

    # ========== Minute 240 (14:59–15:00) ==========
    NumpyOrderIndicator({
        'deal_amount': SingleData({'SH600000': 80, 'SH600003': 150}),
        'trade_value': SingleData({'SH600000': 880, 'SH600003': 2250}),
        'trade_price': SingleData({'SH600000': 880, 'SH600003': 2250}),
        'inner_amount': SingleData({'SH600000': 80, 'SH600003': 150}),
        'trade_dir': SingleData({'SH600000': 1, 'SH600003': 1}),
        # ...
    }),
]
```
https://github.com/microsoft/qlib/blob/main/qlib/backtest/executor.py#L149
https://github.com/microsoft/qlib/blob/main/qlib/backtest/account.py#L143
https://github.com/microsoft/qlib/blob/main/qlib/backtest/__init__.py#L212
markdown

## Explanation of `reset_common_infra` Method

The `reset_common_infra` method is a key part of Qlib's nested executor architecture. It synchronizes shared infrastructure across layers and handles the `trade_account` using a **shallow copy** trick to achieve:

- All layers **share the same real-time position** (cash and stock holdings are synchronized)
- Each layer maintains **independent metrics** (portfolio metrics, trading indicators, historical positions)

### Method Signature (simplified)

```python
def reset_common_infra(self, common_infra: CommonInfrastructure, copy_trade_account: bool = False) -> None:

Line-by-Line Breakdownpython

if not hasattr(self, "common_infra"):
    self.common_infra = common_infra
else:
    self.common_infra.update(common_infra)

Assign or update the shared infrastructure (common_infra)
Ensures the current executor always has the latest shared components (account, exchange, etc.)

python

self.level_infra.reset_infra(common_infra=self.common_infra)

Syncs the updated common_infra to the current layer's sub-infrastructure (level_infra)
Important for nested executors to propagate shared objects downward

python

if common_infra.has("trade_account"):
    self.trade_account: Account = (
        copy.copy(common_infra.get("trade_account"))
        if copy_trade_account
        else common_infra.get("trade_account")
    )
    self.trade_account.reset(freq=self.time_per_step, port_metr_enabled=self.generate_portfolio_metrics)

Core logic – shallow copy decision:If copy_trade_account=True (typical for inner/nested layers):Perform a shallow copy (copy.copy) of the parent account
Shared: current_position (the actual holdings object) → all layers see the same cash/stock changes in real time
Independent: portfolio_metrics, hist_positions, indicator → recreated as new objects

If copy_trade_account=False (typical for the top-level executor):Directly reference the parent account (no copy)

Finally, call reset(...) on the (possibly copied) account:Sets frequency (freq=self.time_per_step)
Enables/disables portfolio metrics (port_metr_enabled)

What Happens in Account.reset_report (called during reset)python

self.portfolio_metrics = PortfolioMetrics(freq, benchmark_config)
self.hist_positions = {}

if ...:
    self.current_position.fill_stock_value(...)

self.indicator = Indicator()

These lines recreate:A new portfolio_metrics object (portfolio-level metrics history)
An empty hist_positions dict (daily position snapshots)
A new indicator object (trading execution metrics: ffr, pa, pos, etc.)

→ These are independent per layer after shallow copy.Shallow Copy vs No Copy – Data ExampleInitial state (top-level account):Cash: 1,000,000
Holdings: none
portfolio_metrics: day-level container A
indicator: day-level trading metrics A

Case A: Inner layer uses shallow copy (copy_trade_account=True) – Recommendedpython

inner_account = copy.copy(outer_account)

# inner_account.current_position is the SAME object as outer_account.current_position
# But:
inner_account.portfolio_metrics  # new independent container B
inner_account.indicator          # new independent Indicator B

Inner layer buys 1,000 shares SH600000 @ 10 yuan:inner_account.current_position updated → cash -= 10,000, holdings +1,000
Outer layer sees the same change immediately (shared position)
Inner layer records minute-level metrics in B
Outer layer continues recording day-level metrics in A (independent)

Case B: Inner layer does NOT copy (copy_trade_account=False) – Incorrectpython

inner_account = outer_account  # direct reference

# inner_account is the same object as outer_account

Inner layer buys 1,000 shares:Position updated (correct, shared)
But when inner layer calls reset_report:inner_account.portfolio_metrics = new minute-level container → overwrites outer's day-level container
inner_account.indicator = new Indicator → overwrites outer's day-level indicator

Result: Outer layer now sees minute-level data → metrics become corrupted and unusable

Why Qlib Uses This DesignReal trading requires all layers to share the same capital and positions (no independent accounts per layer)
But metrics must be layer-specific (outer sees daily portfolio curve, inner sees minute-level execution quality)
Shallow copy perfectly solves this:Shared current_position → real-time synchronization of holdings
Independent portfolio_metrics & indicator → each layer tracks its own view

Summaryreset_common_infra synchronizes shared infrastructure and uses shallow copy on the account (when copy_trade_account=True) to ensure:All layers share the same real-time position (current_position is identical)
Each layer has independent metrics (portfolio_metrics, indicator, hist_positions are recreated)

This is the key mechanism that enables realistic nested backtesting in Qlib (e.g., daily strategy + minute-level execution sharing the same capital).

You can copy the entire block above directly into your GitHub README or documentation. It’s clean, professional, and self-contained.
