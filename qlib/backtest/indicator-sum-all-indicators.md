# Qlib Indicator: How `sum_all_indicators()` and `sum_by_index()` Aggregate Order Metrics

This note explains the following code inside `Indicator._agg_order_trade_info()` in Qlib's backtest module:

```python
all_metric = ["inner_amount", "deal_amount", "trade_price", "trade_value", "trade_cost", "trade_dir"]

self.order_indicator_cls.sum_all_indicators(
    self.order_indicator,
    inner_order_indicators,
    all_metric,
    fill_value=0,
)
```

This code appears in the `atomic=False` path.

A typical nested execution setup is:

```text
Outer step = one day
Inner step = one minute
```

The outer executor does not execute orders directly. Real trades happen inside the inner minute-level executor.

Therefore, the outer executor needs to aggregate multiple inner-step `order_indicator` objects into one outer-step `order_indicator`.

---

## 1. What This Code Does

The purpose of this code is:

```text
Take the same metrics from multiple inner steps,
align them by instrument id,
fill missing values with 0,
sum them instrument by instrument,
and write the aggregated result into the current outer self.order_indicator.
```

The data flow is:

```text
inner_order_indicators
    ↓
sum_all_indicators()
    ↓
self.order_indicator
```

Where:

```text
inner_order_indicators = order indicators from multiple inner steps
self.order_indicator    = the current outer-step order indicator
```

---

## 2. Meaning of Each Argument

Original code:

```python
self.order_indicator_cls.sum_all_indicators(
    self.order_indicator,
    inner_order_indicators,
    all_metric,
    fill_value=0,
)
```

Meaning:

```text
self.order_indicator
= the current outer-step order indicator
= the aggregation result will be written here

inner_order_indicators
= order indicators from multiple inner steps
= the source data

all_metric
= the list of metrics to aggregate

fill_value=0
= if an instrument is missing in an inner step, treat it as 0
```

`all_metric` is:

```python
all_metric = [
    "inner_amount",
    "deal_amount",
    "trade_price",
    "trade_value",
    "trade_cost",
    "trade_dir",
]
```

Each of these metrics will be aggregated one by one.

---

## 3. Important: `trade_price` Is No Longer the Raw Price Here

Before calling `sum_all_indicators()`, Qlib first runs:

```python
def trade_amount_func(deal_amount, trade_price):
    return deal_amount * trade_price

for indicator in inner_order_indicators:
    indicator.transfer(trade_amount_func, "trade_price")
```

This means that, inside each inner indicator:

```text
trade_price
```

is temporarily replaced by:

```text
deal_amount * trade_price
```

In other words, `trade_price` becomes the numerator of a weighted average price.

So when `sum_all_indicators()` later sums `trade_price`, it is not summing raw prices.

It is summing:

```text
deal amount × trade price
```

After the sum is complete, Qlib divides it by the total `deal_amount` to recover the outer-level average trade price.

---

## 4. Example: Three Inner Steps

Assume one outer daily step contains three inner minute steps:

```text
step0 = 09:30
step1 = 09:31
step2 = 09:32
```

Each inner step has already generated its own `order_indicator`.

---

## 5. Data in step0

```text
inner_amount:
SH600000      300
SH600001     -200

deal_amount:
SH600000      300
SH600001     -100

trade_price:
SH600000      3000     # 300 * 10.00
SH600001     -2000     # -100 * 20.00

trade_value:
SH600000      3000
SH600001     -2000

trade_cost:
SH600000      2
SH600001      2

trade_dir:
SH600000      1        # BUY
SH600001      0        # SELL
```

---

## 6. Data in step1

```text
inner_amount:
SH600000      400
SH600001     -200

deal_amount:
SH600000      400
SH600001     -100

trade_price:
SH600000      4040     # 400 * 10.10
SH600001     -1990     # -100 * 19.90

trade_value:
SH600000      4040
SH600001     -1990

trade_cost:
SH600000      2
SH600001      2

trade_dir:
SH600000      1        # BUY
SH600001      0        # SELL
```

---

## 7. Data in step2

```text
inner_amount:
SH600000      300
SH600002      500

deal_amount:
SH600000      300
SH600002      400

trade_price:
SH600000      3060     # 300 * 10.20
SH600002     12000     # 400 * 30.00

trade_value:
SH600000      3060
SH600002     12000

trade_cost:
SH600000      2
SH600002      3

trade_dir:
SH600000      1        # BUY
SH600002      1        # BUY
```

`SH600002` only appears in step2. This makes it easier to see how missing values are handled.

---

## 8. First Step in `sum_all_indicators()`: Collect All Instruments

`sum_all_indicators()` first collects all instruments that appear in the inner indicators.

It uses the first metric in the metric list:

```python
metrics[0] = "inner_amount"
```

So it collects instruments from each inner indicator's `inner_amount.index`.

The instruments in each step are:

```text
step0: SH600000, SH600001
step1: SH600000, SH600001
step2: SH600000, SH600002
```

The union is:

```text
stock_set = {SH600000, SH600001, SH600002}
```

After sorting:

```text
stocks = [SH600000, SH600001, SH600002]
```

All following metrics will be aligned to this `stocks` list.

---

## 9. Second Step in `sum_all_indicators()`: Call `sum_by_index()` for Each Metric

The core logic is equivalent to:

```python
for metric in metrics:
    order_indicator.data[metric] = idd.sum_by_index(
        [indicator.data[metric] for indicator in indicators],
        stocks,
        fill_value,
    )
```

For example, when:

```python
metric = "deal_amount"
```

The input to `sum_by_index()` is:

```python
data_list = [
    step0.data["deal_amount"],
    step1.data["deal_amount"],
    step2.data["deal_amount"],
]

new_index = stocks

fill_value = 0
```

Then `sum_by_index()` aligns the data by instrument id and sums them.

---

## 10. Source Logic of `sum_by_index()`

Simplified source code:

```python
def sum_by_index(data_list, new_index, fill_value=0):
    data_list = [data.to_dict() for data in data_list]
    data_sum = {}

    for id in new_index:
        item_sum = 0

        for data in data_list:
            if id in data and not np.isnan(data[id]):
                item_sum += data[id]
            else:
                item_sum += fill_value

        data_sum[id] = item_sum

    return SingleData(data_sum)
```

It does the following:

```text
1. Convert each SingleData object into a dict.
2. Iterate through the instruments in new_index.
3. For each instrument, look for its value in every inner step.
4. If the value exists and is not NaN, add the real value.
5. If the value is missing or NaN, add fill_value.
6. Return a new SingleData object.
```

---

## 11. Example of `sum_by_index()`

Assume we are aggregating `deal_amount`.

Input data:

```text
step0 deal_amount:
SH600000      300
SH600001     -100

step1 deal_amount:
SH600000      400
SH600001      NaN

step2 deal_amount:
SH600000      300
SH600002      400
```

Equivalent input:

```python
data_list = [
    SingleData({"SH600000": 300, "SH600001": -100}),
    SingleData({"SH600000": 400, "SH600001": np.nan}),
    SingleData({"SH600000": 300, "SH600002": 400}),
]

new_index = ["SH600000", "SH600001", "SH600002"]

fill_value = 0
```

Equivalent matrix:

```text
              step0     step1     step2
SH600000       300       400       300
SH600001      -100       NaN       missing
SH600002       missing   missing   400
```

Because `fill_value=0`, both missing values and NaN values are treated as 0:

```text
              step0     step1     step2
SH600000       300       400       300
SH600001      -100        0         0
SH600002        0         0        400
```

Row-wise sum:

```text
SH600000 = 300 + 400 + 300 = 1000
SH600001 = -100 + 0 + 0 = -100
SH600002 = 0 + 0 + 400 = 400
```

Returned result:

```text
SingleData:

SH600000      1000
SH600001      -100
SH600002       400
```

---

## 12. Aggregating Each Metric in `all_metric`

Now use the full example above to see how each metric is aggregated.

---

### 12.1 Aggregating `inner_amount`

Original data:

```text
step0:
SH600000      300
SH600001     -200

step1:
SH600000      400
SH600001     -200

step2:
SH600000      300
SH600002      500
```

Sum:

```text
SH600000 = 300 + 400 + 300 = 1000
SH600001 = -200 + -200 + 0 = -400
SH600002 = 0 + 0 + 500 = 500
```

Result:

```text
inner_amount:
SH600000      1000
SH600001      -400
SH600002       500
```

Meaning:

```text
inner_amount = total target amount generated by the inner strategy
```

---

### 12.2 Aggregating `deal_amount`

Original data:

```text
step0:
SH600000      300
SH600001     -100

step1:
SH600000      400
SH600001     -100

step2:
SH600000      300
SH600002      400
```

Sum:

```text
SH600000 = 300 + 400 + 300 = 1000
SH600001 = -100 + -100 + 0 = -200
SH600002 = 0 + 0 + 400 = 400
```

Result:

```text
deal_amount:
SH600000      1000
SH600001      -200
SH600002       400
```

Meaning:

```text
deal_amount = total real executed amount from the inner steps
```

---

### 12.3 Aggregating `trade_price`

Here, `trade_price` has already been replaced by:

```text
deal_amount * trade_price
```

Original data:

```text
step0:
SH600000      3000
SH600001     -2000

step1:
SH600000      4040
SH600001     -1990

step2:
SH600000      3060
SH600002     12000
```

Sum:

```text
SH600000 = 3000 + 4040 + 3060 = 10100
SH600001 = -2000 + -1990 + 0 = -3990
SH600002 = 0 + 0 + 12000 = 12000
```

Immediately after `sum_all_indicators()`:

```text
trade_price:
SH600000      10100
SH600001      -3990
SH600002      12000
```

At this point, `trade_price` is not the final average trade price. It is the numerator.

Later, `_agg_order_trade_info()` does:

```text
trade_price = trade_price / deal_amount
```

So:

```text
SH600000 = 10100 / 1000 = 10.10
SH600001 = -3990 / -200 = 19.95
SH600002 = 12000 / 400 = 30.00
```

Final result:

```text
trade_price:
SH600000      10.10
SH600001      19.95
SH600002      30.00
```

Meaning:

```text
trade_price = weighted average execution price from the inner steps
```

---

### 12.4 Aggregating `trade_value`

Original data:

```text
step0:
SH600000      3000
SH600001     -2000

step1:
SH600000      4040
SH600001     -1990

step2:
SH600000      3060
SH600002     12000
```

Sum:

```text
SH600000 = 3000 + 4040 + 3060 = 10100
SH600001 = -2000 + -1990 + 0 = -3990
SH600002 = 0 + 0 + 12000 = 12000
```

Result:

```text
trade_value:
SH600000      10100
SH600001      -3990
SH600002      12000
```

Meaning:

```text
trade_value = total executed trade value from the inner steps
```

---

### 12.5 Aggregating `trade_cost`

Original data:

```text
step0:
SH600000      2
SH600001      2

step1:
SH600000      2
SH600001      2

step2:
SH600000      2
SH600002      3
```

Sum:

```text
SH600000 = 2 + 2 + 2 = 6
SH600001 = 2 + 2 + 0 = 4
SH600002 = 0 + 0 + 3 = 3
```

Result:

```text
trade_cost:
SH600000      6
SH600001      4
SH600002      3
```

Meaning:

```text
trade_cost = total transaction cost from the inner steps
```

---

### 12.6 Aggregating `trade_dir`

Original direction encoding:

```text
BUY  = 1
SELL = 0
```

Original data:

```text
step0:
SH600000      1
SH600001      0

step1:
SH600000      1
SH600001      0

step2:
SH600000      1
SH600002      1
```

Sum:

```text
SH600000 = 1 + 1 + 1 = 3
SH600001 = 0 + 0 + 0 = 0
SH600002 = 0 + 0 + 1 = 1
```

Immediately after `sum_all_indicators()`:

```text
trade_dir:
SH600000      3
SH600001      0
SH600002      1
```

At this point, `trade_dir` is not the final direction. It is only the numeric sum of direction values.

Later, `_agg_order_trade_info()` applies:

```python
trade_dir.apply(Order.parse_dir)
```

The rule is:

```text
> 0  -> BUY
<= 0 -> SELL
```

Final result:

```text
trade_dir:
SH600000      BUY
SH600001      SELL
SH600002      BUY
```

Meaning:

```text
trade_dir = aggregated trade direction
```

---

## 13. Intermediate State Right After `sum_all_indicators()`

Immediately after:

```python
self.order_indicator_cls.sum_all_indicators(...)
```

The outer `self.order_indicator` looks like:

```text
              inner_amount   deal_amount   trade_price   trade_value   trade_cost   trade_dir
SH600000      1000           1000          10100         10100         6            3
SH600001      -400           -200          -3990         -3990         4            0
SH600002      500            400           12000         12000         3            1
```

Two fields are still intermediate values:

```text
trade_price is not the final price yet.
It is the sum of deal_amount * trade_price.

trade_dir is not BUY/SELL yet.
It is the numeric sum of direction values.
```

---

## 14. Fixing `trade_price` After the Sum

Qlib then runs:

```python
def func(trade_price, deal_amount):
    tmp_deal_amount = deal_amount.replace({0: np.nan})
    return trade_price / tmp_deal_amount

self.order_indicator.transfer(func, "trade_price")
```

Calculation:

```text
SH600000 = 10100 / 1000 = 10.10
SH600001 = -3990 / -200 = 19.95
SH600002 = 12000 / 400 = 30.00
```

After this step:

```text
trade_price:
SH600000      10.10
SH600001      19.95
SH600002      30.00
```

---

## 15. Fixing `trade_dir` After the Sum

Qlib then runs:

```python
def func_apply(trade_dir):
    return trade_dir.apply(Order.parse_dir)

self.order_indicator.transfer(func_apply, "trade_dir")
```

After this step:

```text
trade_dir:
SH600000      BUY
SH600001      SELL
SH600002      BUY
```

---

## 16. Final Result of `_agg_order_trade_info()`

After these steps:

```text
1. Temporarily convert trade_price into deal_amount * trade_price.
2. Use sum_all_indicators() to aggregate multiple inner steps.
3. Divide trade_price by deal_amount to recover the weighted average price.
4. Apply Order.parse_dir to convert trade_dir back to BUY/SELL.
```

The final outer `self.order_indicator` is:

```text
              inner_amount   deal_amount   trade_price   trade_value   trade_cost   trade_dir
SH600000      1000           1000          10.10         10100         6            BUY
SH600001      -400           -200          19.95         -3990         4            SELL
SH600002      500            400           30.00         12000         3            BUY
```

---

## 17. Key Takeaways

`sum_all_indicators()` aggregates the same metrics from multiple inner `order_indicator` objects.

It does not compute the final average price.

It does not interpret the final trade direction.

It only does:

```text
Align by instrument id.
Fill missing values with fill_value.
Sum each metric instrument by instrument.
Write the result into the current outer order_indicator.
```

`sum_by_index()` is the lower-level helper that performs the actual index-aligned sum.

Its rule is:

```text
If the instrument exists and the value is not NaN:
    add the real value.

If the instrument is missing:
    add fill_value.

If the instrument exists but the value is NaN:
    add fill_value.
```

In `_agg_order_trade_info()`, `fill_value=0`, so both missing values and NaN values are treated as 0.

The two easiest fields to misunderstand are:

```text
trade_price:
    Inside sum_all_indicators(), it is summing deal_amount * trade_price.
    After the sum, it is divided by deal_amount to get the weighted average execution price.

trade_dir:
    Inside sum_all_indicators(), it is first summed as numeric values.
    After the sum, Order.parse_dir converts it back to BUY/SELL.
```

One-line summary:

```text
sum_all_indicators() is a field-level aggregator.
sum_by_index() is the lower-level index-aligned summation helper.
The final average trade price and final trade direction are fixed after the summation step.
```
