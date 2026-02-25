## BFS Traversal of Configuration Tree – Step-by-Step Execution

[Source Code Link](https://github.com/microsoft/qlib/blob/main/qlib/utils/data.py#L38)

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
