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
    
  
