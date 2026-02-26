## BFS Traversal of Configuration Tree – Step-by-Step Execution

https://github.com/microsoft/qlib/blob/main/qlib/utils/data.py#L38

### Initial State

```python
config = {
    "model": {
        "name": "<MODEL>",
        "params": {
            "lr": "<LR>",
            "depth": 5
        }
    },
    "data": ["train", "<TEST>", "valid"]
}

# Queue initialization
item_queue = [config]  # Queue: [0: config]
top = 0   # Points to the current element to process
tail = 1  # Queue length (last element index + 1)
```

### Round 1 (top=0 < tail=1)

```python
now_item = item_queue[0] = config
top += 1  # top = 1

# config is a dict → item_keys = config.keys() = ['model', 'data']

# Iterate through keys
for key in ['model', 'data']:
    
    # key = 'model'
    value = config['model'] = {'name': '<MODEL>', 'params': {...}}
    # value is a dict → add to queue
    item_queue.append(value)  # Queue: [config, model_dict]
    tail += 1  # tail = 2
    
    # key = 'data'
    value = config['data'] = ['train', '<TEST>', 'valid']
    # value is a list → add to queue
    item_queue.append(value)  # Queue: [config, model_dict, data_list]
    tail += 1  # tail = 3

# End of Round 1: top=1, tail=3, Queue=[config, model_dict, data_list]
```

### Round 2 (top=1 < tail=3)

```python
now_item = item_queue[1] = model_dict
top += 1  # top = 2

# model_dict is a dict → item_keys = ['name', 'params']

# Iterate through keys
for key in ['name', 'params']:
    
    # key = 'name'
    value = model_dict['name'] = '<MODEL>'
    # value is a str → replace placeholder
    model_dict['name'] = try_replace_placeholder('<MODEL>')  # → 'LGBModel'
    
    # key = 'params'
    value = model_dict['params'] = {'lr': '<LR>', 'depth': 5}
    # value is a dict → add to queue
    item_queue.append(value)  # Queue: [config, model_dict, data_list, params_dict]
    tail += 1  # tail = 4

# End of Round 2: top=2, tail=4, Queue=[config, model_dict, data_list, params_dict]
```

### Round 3 (top=2 < tail=4)

```python
now_item = item_queue[2] = data_list
top += 1  # top = 3

# data_list is a list → item_keys = range(3) = [0, 1, 2]

# Iterate through indices
for idx in [0, 1, 2]:
    
    # idx = 0
    value = data_list[0] = 'train'
    # value is a str, but not a placeholder → unchanged
    
    # idx = 1
    value = data_list[1] = '<TEST>'
    # value is a str → replace placeholder
    data_list[1] = try_replace_placeholder('<TEST>')  # → 'test_data'
    
    # idx = 2
    value = data_list[2] = 'valid'
    # value is a str, not a placeholder → unchanged

# No new elements added to queue
# End of Round 3: top=3, tail=4, Queue=[config, model_dict, data_list, params_dict]
```

### Round 4 (top=3 < tail=4)

```python
now_item = item_queue[3] = params_dict
top += 1  # top = 4

# params_dict is a dict → item_keys = ['lr', 'depth']

# Iterate through keys
for key in ['lr', 'depth']:
    
    # key = 'lr'
    value = params_dict['lr'] = '<LR>'
    # value is a str → replace placeholder
    params_dict['lr'] = try_replace_placeholder('<LR>')  # → 0.01
    
    # key = 'depth'
    value = params_dict['depth'] = 5
    # value is an int → not a str, skipped

# No new elements added to queue
# End of Round 4: top=4, tail=4
```

### Loop Ends (top=4, tail=4 → top < tail is false)

### Final Result

```python
config = {
    "model": {
        "name": "LGBModel",        # Replaced
        "params": {
            "lr": 0.01,             # Replaced
            "depth": 5               # Unchanged
        }
    },
    "data": ["train", "test_data", "valid"]  # Replaced
}
```

### Queue State Summary

| Round | top before | top after | tail before | tail after | Processed Node | New Nodes Added |
|-------|-----------|-----------|------------|------------|----------------|-----------------|
| 1 | 0 | 1 | 1 | 3 | config | model_dict, data_list |
| 2 | 1 | 2 | 3 | 4 | model_dict | params_dict |
| 3 | 2 | 3 | 4 | 4 | data_list | None |
| 4 | 3 | 4 | 4 | 4 | params_dict | None |

### Key Points

1. **`top` always points to the next element to be processed**
2. **`tail` always represents the queue length** (increases when new elements are added)
3. When `top == tail`, all elements have been processed
4. BFS ensures level-by-level processing: first level (config), second level (model_dict, data_list), third level (params_dict)

# `flatten_dict` Function Explanation

https://github.com/microsoft/qlib/blob/main/qlib/utils/__init__.py#L681

This function is used to **flatten a nested dictionary**, converting multi-level nested keys into flat keys joined by a separator.

### Function Signature

```python
def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """
    Flatten a nested dict.
    
    Args:
        d (dict): The dictionary to be flattened
        parent_key (str, optional): The parent key, which will be used as a prefix for the new key
        sep (str, optional): The separator for joining keys. Can be a string or FLATTEN_TUPLE
    """
```

### How It Works

The function recursively traverses the dictionary:
- If a value is a dictionary (`MutableMapping`), continue recursion
- Otherwise, add the current key-value pair to the result

### Line-by-Line Code Explanation

```python
items = []  # Store flattened key-value pairs

for k, v in d.items():  # Iterate through all items in the current dictionary
    # 1. Construct the new key
    if sep == FLATTEN_TUPLE:
        # Use tuple as the key
        new_key = (parent_key, k) if parent_key else k
    else:
        # Use string concatenation
        new_key = parent_key + sep + k if parent_key else k
    
    # 2. Process the value
    if isinstance(v, collections.abc.MutableMapping):
        # If the value is a dictionary, process recursively
        items.extend(flatten_dict(v, new_key, sep=sep).items())
    else:
        # If not a dictionary, add directly
        items.append((new_key, v))

return dict(items)  # Convert back to dictionary and return
```

### Example 1: Using String Separator (Default)

```python
from qlib.utils import flatten_dict

nested_dict = {
    'a': 1,
    'c': {
        'a': 2,
        'b': {
            'x': 5,
            'y': 10
        }
    },
    'd': [1, 2, 3]
}

flattened = flatten_dict(nested_dict, sep=".")
print(flattened)
# Output:
# {
#     'a': 1,
#     'c.a': 2,
#     'c.b.x': 5,
#     'c.b.y': 10,
#     'd': [1, 2, 3]
# }
```

### Example 2: Using Tuple as Key

```python
from qlib.utils import flatten_dict, FLATTEN_TUPLE

nested_dict = {
    'a': 1,
    'c': {
        'a': 2,
        'b': {
            'x': 5,
            'y': 10
        }
    },
    'd': [1, 2, 3]
}

flattened = flatten_dict(nested_dict, sep=FLATTEN_TUPLE)
print(flattened)
# Output:
# {
#     'a': 1,
#     ('c', 'a'): 2,
#     ('c', 'b', 'x'): 5,
#     ('c', 'b', 'y'): 10,
#     'd': [1, 2, 3]
# }
```

### Recursion Process Visualization

Using the first example, the recursion process looks like this:

```
Level 1: {'a': 1, 'c': {...}, 'd': [...]}
  ├─ key='a', value=1 → not a dict → add ('a', 1)
  ├─ key='c', value={'a': 2, 'b': {...}} → is a dict → recurse
  │   ├─ Level 2 (parent_key='c'):
  │   │   ├─ key='a', value=2 → not a dict → add ('c.a', 2)
  │   │   └─ key='b', value={'x': 5, 'y': 10} → is a dict → recurse
  │   │       ├─ Level 3 (parent_key='c.b'):
  │   │       │   ├─ key='x', value=5 → add ('c.b.x', 5)
  │   │       │   └─ key='y', value=10 → add ('c.b.y', 10)
  └─ key='d', value=[1,2,3] → not a dict → add ('d', [1,2,3])
```

### Application Scenarios in Qlib

```python
# In experiment management, nested configuration parameters often need to be recorded
config = {
    "model": {
        "class": "LGBModel",
        "params": {
            "learning_rate": 0.01,
            "num_leaves": 31
        }
    },
    "dataset": {
        "name": "Alpha158",
        "kwargs": {
            "windows": 20
        }
    }
}

# Flattening makes storage and querying easier
flat_config = flatten_dict(config)
# {
#     'model.class': 'LGBModel',
#     'model.params.learning_rate': 0.01,
#     'model.params.num_leaves': 31,
#     'dataset.name': 'Alpha158',
#     'dataset.kwargs.windows': 20
# }
```

### Parameter Description

| Parameter | Type | Description |
|-----------|------|-------------|
| **d** | `dict` | The nested dictionary to be flattened |
| **parent_key** | `str` | Parent key, used internally during recursion |
| **sep** | `str` | Separator for joining keys. Can be a string or `FLATTEN_TUPLE` |

### Special Value `FLATTEN_TUPLE`

`FLATTEN_TUPLE` is a special marker. When `sep` equals this value, tuples are used as keys instead of strings:

```python
# Definition (usually in qlib/utils/__init__.py)
FLATTEN_TUPLE = "__flatten_tuple__"
```

This is useful when you need to preserve the hierarchical structure of keys but don't want to use string concatenation.
