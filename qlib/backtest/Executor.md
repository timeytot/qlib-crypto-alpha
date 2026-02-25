# Qlib Executor Infrastructure: Data Structure and Time Range Control

This document explains the executor infrastructure in Qlib, focusing on nested backtesting scenarios, object relationships, and time range control mechanisms.

## 1. Data Structure Diagram: Nested Backtesting Scenario

Below is a complete data structure relationship diagram based on the execution process of `BaseExecutor.reset_common_infra()`, illustrating object reference relationships for top-level (daily frequency) and inner-level (minute frequency) Executors.

```
Global Shared Resources
└── common_infra_global (CommonInfrastructure object)
    ├── trade_account → Account(init_cash=100000)   ← Shared by all levels (same instance)
    └── trade_exchange → Exchange(...)              ← Shared by all levels (same instance)

Top-Level Executor (NestedExecutor, daily frequency)
├── self.common_infra ───────────────────────────► common_infra_global   (direct reference)
├── self.level_infra (LevelInfrastructure)
│   ├── common_infra ───────────────────────────► common_infra_global
│   ├── executor ───────────────────────────────► Top-level NestedExecutor itself
│   ├── trade_calendar → Daily TradeCalendarManager (e.g., 2025-01-02 ~ 2025-01-10)
│   └── sub_level_infra ───────────────────────► Inner-level level_infra (below)
│
├── self.inner_executor → Inner SimulatorExecutor (30-minute frequency)
│   ├── self.common_infra ──────────────────────► common_infra_global   (reference to same object)
│   ├── self.level_infra (LevelInfrastructure)
│   │   ├── common_infra ───────────────────────► common_infra_global
│   │   ├── executor ───────────────────────────► Inner SimulatorExecutor itself
│   │   └── trade_calendar → 30-minute TradeCalendarManager
│   │       (reset to current day's 30-minute interval on each outer step)
│   │
│   └── self.trade_account → Same Account object (shared reference)
│
└── self.inner_strategy
    └── Accesses inner_executor's trade_calendar, common_infra via level_infra
```

### Key Points:
- **Global Resources**: `trade_account` and `trade_exchange` are shared SINGLE instances across all levels
- **LevelInfrastructure**: Each executor level has its own infrastructure with:
  - Reference to global common_infra
  - Reference to its own executor
  - Its own trade_calendar (appropriate frequency)
  - Reference to sub_level_infra (for nested executors)
- **Inner Executor**: Created and managed by top-level NestedExecutor, reset each outer step

---

## 2. Time Range Control: From User Input to Step Indices

### Core Method Reference
[`executor.py#L432`](https://github.com/microsoft/qlib/blob/main/qlib/backtest/executor.py#L432): `start_idx, end_idx = get_start_end_idx(sub_cal, trade_decision)`

### The Flow: How Daily Time Range Maps to Intraday Indices

```
Outer-level Decision (daily frequency)
└── Contains trade_range = TradeRangeByTime("09:30", "14:30")
    └── self.start_time = time(9, 30, 0)      ← User-defined fixed daily start time
        self.end_time   = time(14, 30, 0)     ← User-defined fixed daily end time

NestedExecutor starts inner loop
└── Calls get_start_end_idx(sub_cal, outer_decision)
    └── sub_cal is the inner_calendar (inner-level TradeCalendarManager)

get_start_end_idx calls
└── outer_decision.get_range_limit(inner_calendar=inner_calendar)

_get_range_limit calls
└── self.trade_range(inner_calendar)   ← Executes TradeRangeByTime.__call__

TradeRangeByTime.__call__ executes the key three lines:
1. start_date = trade_calendar.start_time.date()
   → Extracts current loop's date from inner_calendar (e.g., 2025-01-02)

2. val_start = concat_date_time(start_date, self.start_time)
   → Combines "today's date" + "user-defined daily start time" into full timestamp
   → 2025-01-02 09:30:00
   
   val_end = concat_date_time(start_date, self.end_time)
   → 2025-01-02 14:30:00

3. return trade_calendar.get_range_idx(val_start, val_end)
   → Looks up step indices corresponding to 09:30 and 14:30 in inner_calendar sequence
   → Returns (start_idx, end_idx), e.g., (19, 29)
```

### Why Must Inner Calendar Be Passed?

**Because**: `TradeRangeByTime` only stores hours and minutes (09:30, 14:30) — it has no knowledge of which actual date it is processing.

- Only `inner_calendar.start_time` knows whether current loop is processing 2025-01-02 or 2025-01-03
- Different dates produce different full timestamps, resulting in different indices

### Example: Same Time Range, Different Dates

| Date | Start Timestamp | End Timestamp | Start Index | End Index |
|------|-----------------|---------------|-------------|-----------|
| 2025-01-02 | 2025-01-02 09:30:00 | 2025-01-02 14:30:00 | 19 | 29 |
| 2025-01-03 | 2025-01-03 09:30:00 | 2025-01-03 14:30:00 | 20 | 30 |

### One-Sentence Summary

Yes — it uses the date from `inner_calendar` (`trade_calendar.start_time.date()`) to determine "which day today is", combines it with the user-preset `self.start_time` / `self.end_time` (fixed daily hours/minutes) from `TradeRangeByTime` to form complete datetimes, which are finally converted into step indices for the inner executor. This precisely controls which high-frequency bars are allowed to trade on any given day.

This design is extremely elegant: the user only needs to set the window once ("every day from 09:30 to 14:30"), and the framework automatically adapts it to every specific date and inner-level frequency.

---

## 3. Alignment Mode Control

### Method Reference
[`executor.py#L433`](https://github.com/microsoft/qlib/blob/main/qlib/backtest/executor.py#L433):
```python
if not self._align_range_limit or start_idx <= sub_cal.get_trade_step() <= end_idx:
```

### Two Alignment Modes

```python
if self._align_range_limit:  
    # Strict mode: MUST be inside allowed range
    if start_idx <= sub_cal.get_trade_step() <= end_idx:
        execute inner strategy and trade
    else:
        only advance time (sub_cal.step()), no trading
else:
    # Relaxed mode: ignore range limit completely
    execute inner strategy and trade on EVERY step
```

### Mode Comparison

| Mode | `_align_range_limit` | Behavior | Use Case |
|------|---------------------|----------|----------|
| **Strict** | `True` | Trade only within [start_idx, end_idx]; outside range → advance time only | Realistic simulation respecting market hours |
| **Relaxed** | `False` | Trade on EVERY step, ignoring time range | Testing, debugging, continuous markets |

---

## 4. Complete Initialization Chain

### How Start/End Times Propagate Through the System

```
User creates TradeRangeByTime("09:30", "14:30")
    ↓ (initialization: self.start_time / self.end_time)
TradeDecisionWO(trade_range=trade_range)
    ↓ (outer decision passed to NestedExecutor)
NestedExecutor._collect_data
    ↓
get_start_end_idx(sub_cal, outer_decision)
    ↓
outer_decision.get_range_limit(inner_calendar=sub_cal)
    ↓
outer_decision.trade_range(sub_cal)   ← TradeRangeByTime.__call__
    ↓
trade_calendar.get_range_idx("2025-01-02 09:30", "2025-01-02 14:30")
    ↓
return (start_idx, end_idx)   # (19, 29)
```

### Code Example: Setting Up Time-Restricted Trading

```python
from qlib.backtest.decision import TradeRangeByTime, TradeDecisionWO, Order
from qlib.constant import OrderDir

# 1. Create time range (fixed daily window)
trade_range = TradeRangeByTime(
    start_time="09:30",   
    end_time="14:30"     
)
# Internally: self.start_time = time(9, 30, 0)
#            self.end_time   = time(14, 30, 0)

# 2. Create outer decision with this time range
outer_decision = TradeDecisionWO(
    order_list=[
        Order(
            stock_id="SH600000",
            amount=10000,
            direction=OrderDir.BUY,
        )
    ],
    strategy=outer_strategy,      
    trade_range=trade_range        
)

# 3. Inside NestedExecutor main loop
from qlib.backtest.utils import get_start_end_idx

while not self.inner_executor.finished():
    sub_cal = self.inner_executor.trade_calendar
    
    # Get today's start/end indices based on inner calendar
    start_idx, end_idx = get_start_end_idx(sub_cal, trade_decision)
    
    # Check if current step is within allowed range
    if not self._align_range_limit or start_idx <= sub_cal.get_trade_step() <= end_idx:
        # Execute strategy and trade
        ...
    else:
        # Just advance time, no trading
        sub_cal.step()
```

### Key Insight

The time range is defined **once** at the user level but applied **dynamically** to each trading day based on the inner calendar's current date. This creates a powerful abstraction where:

- **User specifies**: "Trade daily from 09:30 to 14:30"
- **System interprets**: For 2025-01-02 → trade indices 19-29; for 2025-01-03 → trade indices 20-30; etc.

This handles varying intraday bar counts across different days automatically!
