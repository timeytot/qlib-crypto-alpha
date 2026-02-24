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

Why is there an extra res[1].append(...) at the end?
Because the loop can only process decisions that have a next same-level decision as a boundary. The last same-level decision has no next decision to trigger its processing, so it needs to be handled separately after the loop.

Analogy
Imagine organizing a stack of documents grouped by chapters:

text
Documents: [Chapter1, Section1, Section2, Chapter2, Section3, Section4, Section5]
Your organizing logic:

Iterate through documents. When encountering a new chapter, package the previous chapter and its contents

But the last chapter has no next chapter to trigger the packaging, so you need to handle it separately after the loop

Code Execution Visualization
python
decisions = [day_1, min_1_1, min_1_2, day_2, min_2_1, min_2_2, min_2_3]
# indices:     0      1        2       3      4        5        6
Inside the Loop (when encountering the next same-level decision)
text
When i=3, we find day_2 → process day_1 and its sub-decisions [min_1_1, min_1_2]
    res[1].append((day_1, format_decisions([min_1_1, min_1_2])))
    last_dec_idx = 3
After the Loop
At this point:

last_dec_idx = 3 (pointing to the last day-level decision)

Remaining unprocessed decisions: decisions[4:] = [min_2_1, min_2_2, min_2_3]

There is no next day-level decision to trigger processing

Therefore, we need to handle the last one separately
python
# Manually process the last day_2 and all its sub-decisions
res[1].append((day_2, format_decisions([min_2_1, min_2_2, min_2_3])))
What Would Happen Without This Line?
python
# After the loop, res would only contain:
res = ("day", [(day_1, ("1min", [(min_1_1, None), (min_1_2, None)]))])

# day_2 and all its sub-decisions would be completely lost!
The Complete Process
Step	What Happens	Result
Loop	When finding day_2, process day_1 and its children	(day_1, sub_tree) added to result
After Loop	No more day-level decisions to trigger processing	Need to manually process day_2
Final Line	Process day_2 and all remaining decisions	(day_2, sub_tree) added to result
Common Design Pattern
This pattern is known as "loop processing + trailing edge handling" or "process boundaries + final element". It's commonly used when you need to split data based on boundaries:
