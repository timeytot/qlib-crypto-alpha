## `deepcopy_basic_type` Function – Full Data Shape Before & After

[Source Code Link](https://github.com/microsoft/qlib/blob/main/qlib/utils/data.py#L38)https://github.com/microsoft/qlib/blob/main/qlib/utils/data.py#L38

The `deepcopy_basic_type` function creates **new container structures** (dict, list, tuple) while **sharing references** to their contents (primitives and complex objects). This enables fast, safe config duplication in Qlib without copying expensive objects like models or datasets.

### Original Config (before copy)

```python
class ExpensiveModel:
    def __init__(self, learning_rate=0.01):
        self.learning_rate = learning_rate

some_expensive_model = ExpensiveModel(learning_rate=0.01)

config = {
    "topk": 50,                                 # int (immutable primitive)
    "n_drop": 5,                                # int
    "signal": some_expensive_model,             # shared reference to model
    "params": {                                 # nested dict
        "horizon": 5,
        "alpha": 0.9
    },
    "labels": [                                 # list of str (immutable)
        "Ref($close, -2)/$close - 1",
        "Ref($close, -5)/$close - 1"
    ],
    "extra": (1.0, 2.0)                         # tuple (immutable)
}
```

Memory layout (simplified):

```
config @ 0xA (dict)
├── "topk" → 50 @ 0xB (int)
├── "n_drop" → 5 @ 0xC (int)
├── "signal" → model @ 0xD (shared object)
├── "params" → dict @ 0xE
│   ├── "horizon" → 5 @ 0xF (int)
│   └── "alpha" → 0.9 @ 0x10 (float)
├── "labels" → list @ 0x11
│   ├── 0 → str @ 0x12
│   └── 1 → str @ 0x13
└── "extra" → tuple @ 0x14
    ├── 0 → 1.0 @ 0x15 (float)
    └── 1 → 2.0 @ 0x16 (float)
```

### After `new_config = deepcopy_basic_type(config)`

```python
new_config = {
    "topk": 50,                                 # same int value (shared)
    "n_drop": 5,
    "signal": some_expensive_model,             # same model object (shared reference)
    "params": {                                 # NEW dict object
        "horizon": 5,
        "alpha": 0.9
    },
    "labels": [                                 # NEW list object
        "Ref($close, -2)/$close - 1",
        "Ref($close, -5)/$close - 1"
    ],
    "extra": (1.0, 2.0)                         # NEW tuple object
}
```

Memory layout after copy (simplified):

```
new_config @ 0x100 (NEW dict)
├── "topk" → 50 @ 0xB (same as original)
├── "n_drop" → 5 @ 0xC (same)
├── "signal" → model @ 0xD (same object!)
├── "params" → NEW dict @ 0x101
│   ├── "horizon" → 5 @ 0xF (shared)
│   └── "alpha" → 0.9 @ 0x10 (shared)
├── "labels" → NEW list @ 0x102
│   ├── 0 → str @ 0x12 (shared)
│   └── 1 → str @ 0x13 (shared)
└── "extra" → NEW tuple @ 0x103
    ├── 0 → 1.0 @ 0x15 (shared)
    └── 1 → 2.0 @ 0x16 (shared)
```

### Summary Table: Copied vs Shared

| Element Type | Copied? (New Object) | Shared? (Original Reference) | Memory Address Change? | Modification Impact on Original |
|--------------|---------------------|------------------------------|------------------------|----------------------------------|
| **Top-level dict** | Yes | No | Yes | Structure changes independent |
| **Nested dict ("params")** | Yes | No | Yes | Structure changes independent |
| **Nested list ("labels")** | Yes | No | Yes | Structure changes independent |
| **Nested tuple ("extra")** | Yes | No | Yes | Structure changes independent |
| **Primitives (int, float, str)** | No (immutable) | Yes | No | Reassignment → no impact |
| **Complex object (model)** | No | Yes | No | In-place changes → affects all |

### Modification Examples

**Modify primitive (int/float/str) → safe, no impact**
```python
new_config["topk"] = 30
# config["topk"] still 50
```

**Modify nested container → only affects new copy**
```python
new_config["params"]["horizon"] = 10
# config["params"]["horizon"] still 5
```

**Modify shared mutable object → affects both**
```python
new_config["signal"].learning_rate = 0.001
# config["signal"].learning_rate also becomes 0.001 (same object!)
```

**To avoid affecting original: reassign**
```python
new_config["signal"] = copy.deepcopy(some_expensive_model)  # explicit deep copy if needed
```

### One-Sentence Summary

`deepcopy_basic_type` creates new containers (dict/list/tuple) for safe structural changes while sharing references to contents (primitives immutable → safe, mutable objects like models → changes propagate), enabling fast config duplication without duplicating expensive objects.
