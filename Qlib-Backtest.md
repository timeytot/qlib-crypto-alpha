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
    
  
