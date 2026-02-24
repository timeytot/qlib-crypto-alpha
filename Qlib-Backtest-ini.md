# `format_decisions` Function Explanation
https://github.com/microsoft/qlib/blob/main/qlib/backtest/__init__.py#L312

This function converts a flat list of trading decisions into a tree structure that reflects the nested execution hierarchy.

### Function Signature

```python
def format_decisions(
    decisions: List[BaseTradeDecision],
) -> Optional[Tuple[str, List[Tuple[BaseTradeDecision, Union[Tuple, None]]]]]:
```

### Input: Flat Decision List

When using `collect_data()` in a nested backtest (e.g., daily outer executor with minute-level inner executor), the decisions are collected in chronological order as a flat list:

```python
decisions = [
    day_1,      # Day 1 daily decision (freq="day")
    min_1_1,    # Day 1 minute 1 decision (freq="1min")  
    min_1_2,    # Day 1 minute 2 decision (freq="1min")
    day_2,      # Day 2 daily decision (freq="day")
    min_2_1,    # Day 2 minute 1 decision (freq="1min")
    min_2_2,    # Day 2 minute 2 decision (freq="1min")
    min_2_3,    # Day 2 minute 3 decision (freq="1min")
]
```

### Output: Tree Structure

The function reorganizes this flat list into a hierarchical tree:

```python
(
    "day",  # Root frequency
    [
        (day_1, (  # First daily decision with its children
            "1min",  # Child frequency
            [
                (min_1_1, None),  # Leaf node (no children)
                (min_1_2, None)   # Leaf node (no children)
            ]
        )),
        (day_2, (  # Second daily decision with its children
            "1min",
            [
                (min_2_1, None),
                (min_2_2, None),
                (min_2_3, None)
            ]
        ))
    ]
)
```

### Code Explanation with Data Examples

```python
def format_decisions(decisions):
    # Empty list returns None (leaf node termination)
    if len(decisions) == 0:
        return None

    # Get frequency from first decision (e.g., "day")
    cur_freq = decisions[0].strategy.trade_calendar.get_freq()

    # Initialize result: (frequency, list of children)
    res: Tuple[str, list] = (cur_freq, [])
    last_dec_idx = 0  # Track last decision at current frequency level

    # Iterate through decisions starting from index 1
    for i, dec in enumerate(decisions[1:], 1):
        # When we find another decision at the same frequency level
        if dec.strategy.trade_calendar.get_freq() == cur_freq:
            # Extract sub-decisions between last and current
            sub_decisions = decisions[last_dec_idx + 1 : i]
            
            # Recursively format sub-decisions
            sub_tree = format_decisions(sub_decisions)
            
            # Add to result: (decision, its sub-tree)
            res[1].append((decisions[last_dec_idx], sub_tree))
            
            # Update last index
            last_dec_idx = i

    # Handle the last decision at current frequency level
    last_sub_decisions = decisions[last_dec_idx + 1 :]
    last_sub_tree = format_decisions(last_sub_decisions)
    res[1].append((decisions[last_dec_idx], last_sub_tree))

    return res
```

### Step-by-Step Execution

#### Initial State
```python
decisions = [day_1, min_1_1, min_1_2, day_2, min_2_1, min_2_2, min_2_3]
# indices:    0      1        2       3      4        5        6
cur_freq = "day"  # from decisions[0]
last_dec_idx = 0
res = ("day", [])
```

#### Iteration 1 (i=1, dec=min_1_1)
- `min_1_1.freq = "1min"` ≠ "day" → skip

#### Iteration 2 (i=2, dec=min_1_2)
- `min_1_2.freq = "1min"` ≠ "day" → skip

#### Iteration 3 (i=3, dec=day_2)
- `day_2.freq = "day"` == "day" → found next daily decision
- `sub_decisions = decisions[1:3] = [min_1_1, min_1_2]`
- Recursive call `format_decisions([min_1_1, min_1_2])`:

```python
# Inside recursion
cur_freq = "1min"
last_dec_idx = 0
# Iterate: i=1, dec=min_1_2
# min_1_2.freq = "1min" == "1min"
sub_tree = format_decisions([])  # Returns None
res[1].append((min_1_1, None))
last_dec_idx = 1
# Handle last: sub_tree = format_decisions([]) = None
res[1].append((min_1_2, None))
return ("1min", [(min_1_1, None), (min_1_2, None)])
```

- Back to outer: `res[1].append((day_1, ("1min", [(min_1_1, None), (min_1_2, None)])))`
- `last_dec_idx = 3`

#### After Loop
```python
last_sub_decisions = decisions[4:] = [min_2_1, min_2_2, min_2_3]
last_sub_tree = format_decisions([min_2_1, min_2_2, min_2_3])
# Returns: ("1min", [(min_2_1, None), (min_2_2, None), (min_2_3, None)])
res[1].append((day_2, last_sub_tree))
```

### Final Return Value

```python
(
    "day",
    [
        (day_1, (
            "1min",
            [
                (min_1_1, None),
                (min_1_2, None)
            ]
        )),
        (day_2, (
            "1min",
            [
                (min_2_1, None),
                (min_2_2, None),
                (min_2_3, None)
            ]
        ))
    ]
)
```

### Key Points

| Concept | Description |
|---------|-------------|
| **Tree Structure** | `(frequency, [(decision, sub_tree), ...])` |
| **Leaf Node** | `(decision, None)` - no sub-decisions |
| **Frequency** | Determined by `strategy.trade_calendar.get_freq()` |
| **Recursion** | Sub-decisions are formatted recursively |
| **Empty List** | Returns `None` (terminates recursion) |

### Usage Example

```python
from qlib.backtest import collect_data, format_decisions

# Collect decisions during backtest
decisions = []
for decision in collect_data(...):
    decisions.append(decision)

# Format into tree structure
decision_tree = format_decisions(decisions)

# Traverse the tree
def print_tree(node, level=0):
    if node is None:
        return
    freq, children = node
    print("  " * level + f"Frequency: {freq}")
    for decision, sub_tree in children:
        print("  " * (level + 1) + f"Decision: {decision}")
        if sub_tree:
            print_tree(sub_tree, level + 2)

print_tree(decision_tree)
```
