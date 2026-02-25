markdown

https://github.com/microsoft/qlib/blob/main/qlib/utils/data.py#L38

## `deepcopy_basic_type` Function – Full Data Shape Before & After

The `deepcopy_basic_type` function creates a **new container structure** (dict, list, tuple) while **sharing references** to the original contents (primitives and complex objects). This allows fast, safe config duplication in Qlib without copying expensive objects like models or datasets.

### Original Config (before copy)

```python
some_expensive_model = ExpensiveModel(learning_rate=0.01)  # complex mutable object

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

Memory layout (simplified):

config @ 0xA (dict)
├── "topk" → 50 @ 0xB (int)
├── "signal" → model @ 0xC (shared)
├── "params" → dict @ 0xD
│   ├── "horizon" → 5 @ 0xE
│   └── "alpha" → 0.9 @ 0xF
├── "labels" → list @ 0x10
│   ├── 0 → str @ 0x11
│   └── 1 → str @ 0x12
└── "extra" → tuple @ 0x13
    ├── 0 → 1.0
    └── 1 → 2.0

After new_config = deepcopy_basic_type(config)python

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

Memory layout after copy (simplified):

new_config @ 0x100 (NEW dict)
├── "topk" → 50 @ 0xB (same as original)
├── "signal" → model @ 0xC (same object!)
├── "params" → NEW dict @ 0x101
│   ├── "horizon" → 5 @ 0xE (shared)
│   └── "alpha" → 0.9 @ 0xF (shared)
├── "labels" → NEW list @ 0x102
│   ├── 0 → str @ 0x11 (shared)
│   └── 1 → str @ 0x12 (shared)
└── "extra" → NEW tuple @ 0x103
    ├── 0 → 1.0 (shared)
    └── 1 → 2.0 (shared)

Summary Table: Copied vs SharedElement Type
Copied? (New Object)
Shared? (Original Reference)
Memory Address Change?
Modification Impact on Original
Top-level dict
Yes
No
Yes
Structure changes independent
Nested dict ("params")
Yes
No
Yes
Structure changes independent
Nested list ("labels")
Yes
No
Yes
Structure changes independent
Nested tuple ("extra")
Yes
No
Yes
Structure changes independent
Primitives (int, float, str)
No (immutable)
Yes
No
Reassignment → no impact
Complex object (model)
No
Yes
No
In-place changes → affects all

What Happens When You Modify?Modify primitive (int/float/str) → safe, no impact on originalpython

new_config["topk"] = 30
# config["topk"] still 50

Modify nested container → only affects new copypython

new_config["params"]["horizon"] = 10
# config["params"]["horizon"] still 5

Modify shared mutable object → affects bothpython

new_config["signal"].learning_rate = 0.001
# config["signal"].learning_rate also becomes 0.001 (same object!)

To avoid: reassign the keypython

new_config["signal"] = copy.deepcopy(some_expensive_model)  # explicit deep copy if needed

One-Sentence Summarydeepcopy_basic_type creates new containers (dict/list/tuple) for safe structural changes while sharing references to contents (primitives immutable → safe, mutable objects like models → changes propagate), enabling fast config duplication without duplicating expensive objects.

You can copy the entire block above directly into your GitHub `.md` file. It includes the GitHub link at the top, full data shape before & after, memory layout, modification examples, and summary table.

Let me know if you want adjustments (e.g., shorter, more examples, different model class, etc.)!

