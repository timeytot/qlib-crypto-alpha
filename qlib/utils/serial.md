## `Serializable._is_kept` and `__getstate__` Logic

**Source file**: [qlib/utils/serial.py#L38](https://github.com/microsoft/qlib/blob/main/qlib/utils/serial.py#L38)

### Core Methods

```python
def _is_kept(self, key):
    if key in self.config_attr:
        return False
    if key in self._get_attr_list("include"):
        return True
    if key in self._get_attr_list("exclude"):
        return False
    return self.dump_all or not key.startswith("_")

def __getstate__(self) -> dict:
    return {k: v for k, v in self.__dict__.items() if self._is_kept(k)}
```

### Helper Method: `_get_attr_list`

```python
def _get_attr_list(self, attr_type: str) -> list:
    """
    Get the list of attributes for inclusion or exclusion.

    Parameters
    ----------
    attr_type : str
        "include" or "exclude"

    Returns
    -------
    list:
        List of attribute names.
    """
    if hasattr(self, f"_{attr_type}"):
        res = getattr(self, f"_{attr_type}", [])
    else:
        res = getattr(self.__class__, f"{attr_type}_attr", [])
    if res is None:
        return []
    return res
```

### What is `self.__dict__.items()`?

`self.__dict__` is a special Python attribute that stores **all instance attributes of an object** as a dictionary.

#### Code Example

```python
class MyClass:
    def __init__(self):
        self.data = [1, 2, 3]
        self._include = ["data"]
        self._exclude = ["_cache"]
        self._cache = {"temp": 123}

obj = MyClass()
print(obj.__dict__)
```

**Output**:
```python
{
    'data': [1, 2, 3],
    '_include': ['data'],
    '_exclude': ['_cache'],
    '_cache': {'temp': 123}
}
```

### Understanding the Logic

#### Class Definition
```python
# config_attr = ["_include", "_exclude"]

if key in self.config_attr:
    return False
```

#### Data Example

Assume an object with the following attributes:

```python
obj = MySerializable()
obj.data = [1, 2, 3]        # Business data
obj._include = ["data"]      # Rule: only save 'data'
obj._exclude = ["_cache"]    # Rule: exclude '_cache'
obj._cache = {"temp": 123}   # Temporary data
```

#### `__getstate__()` Execution

```python
def __getstate__(self):
    # Iterate through all attributes in obj.__dict__
    return {k: v for k, v in self.__dict__.items() if self._is_kept(k)}
```

For each attribute, `_is_kept()` is called:

| Attribute | `_is_kept()` Evaluation | Result |
|-----------|-------------------------|--------|
| `"data"` | Not in `config_attr`, continue checking | ✅ **Saved** (最终 True) |
| **`"_include"`** | **In `config_attr` → direct `return False`** | ❌ **Not saved** |
| **`"_exclude"`** | **In `config_attr` → direct `return False`** | ❌ **Not saved** |
| `"_cache"` | Not in `config_attr`, continue checking | ❌ Not saved (starts with `_` and not in include list) |

#### Serialization Result

```python
state = obj.__getstate__()
print(state)
# Output: {'data': [1, 2, 3]}
```

### Why This Design?

If `_include` were saved, it would cause problems:

```python
# Assuming _include was incorrectly saved
state = {'data': [1, 2, 3], '_include': ['data']}

# After loading
loaded = MySerializable()
loaded.__setstate__(state)
# loaded._include = ['data']  ← The rule becomes fixed!
```

### Detailed Logic Breakdown

| Code | What it Queries | What it Checks | Analogy |
|------|-----------------|----------------|---------|
| `if key in self.config_attr` | Class attribute list | Whether the **key name** is `"_include"` or `"_exclude"` | Checking "ID card" |
| `if key in self._get_attr_list("include")` | Value of `_include` | Whether the **key name** is in the inclusion list | Checking the "whitelist" |

#### Data Example for Comparison

```python
class MyClass:
    config_attr = ["_include", "_exclude"]  # Class attribute list (key names)
    
    def __init__(self):
        self._include = ["data", "params"]   # Value of _include (key values)
        self.data = [1, 2, 3]
        self.params = {"lr": 0.01}
```

#### Evaluating `"data"`

```python
# First line: if "data" in self.config_attr?
# config_attr = ["_include", "_exclude"] → "data" is NOT in it → False

# Second line: if "data" in self._get_attr_list("include")?
# self._get_attr_list("include") = ["data", "params"] → "data" IS in it → True
# Result: Save "data"
```

#### Evaluating `"_include"`

```python
# First line: if "_include" in self.config_attr?
# config_attr = ["_include", "_exclude"] → "_include" IS in it → True
# Directly returns False, second line is not executed
# Result: Do NOT save "_include"
```

### Analogy for Understanding

- **`config_attr`** acts like a **blacklist** – it contains the **attribute names themselves** that should never be saved
- **The value of `_include`** acts like a **whitelist** – it contains the **names of other attributes** that should be saved

Therefore:
- `"_include"` is in the blacklist → not saved
- `"data"` is not in the blacklist → check the whitelist → it is in the whitelist → saved

### Summary

| Code | What it Queries | Purpose |
|------|-----------------|---------|
| `if key in self.config_attr` | Checks the **class attribute list** | Excludes `"_include"` and `"_exclude"` themselves from being saved |
| `if key in self._get_attr_list("include")` | Checks the **value of `_include`** | Includes attributes explicitly marked for saving |
| `if key in self._get_attr_list("exclude")` | Checks the **value of `_exclude`** | Excludes attributes explicitly marked for exclusion |
| `self.dump_all or not key.startswith("_")` | Fallback rule | Saves non-private attributes by default |

## `config` Method Explanation

**Source file**: [qlib/utils/serial.py#L81](https://github.com/microsoft/qlib/blob/main/qlib/utils/serial.py#L81)

This method is used to **configure the behavior of a serializable object**, determining which attributes are saved or excluded during serialization, with optional recursive application to child objects.

### Method Signature

```python
def config(self, recursive=False, **kwargs):
    """
    Configure the serializable object.

    Parameters
    ----------
    kwargs : 
        dump_all : bool      # Whether to save all attributes (including private ones)
        exclude : list       # List of attributes explicitly NOT to be dumped
        include : list       # List of attributes explicitly TO be dumped
    recursive : bool         # Whether to apply configuration recursively to child objects
    """
```

### Line-by-Line Code Explanation

#### 1. Processing Configuration Parameters

```python
keys = {"dump_all", "exclude", "include"}
for k, v in kwargs.items():
    if k in keys:
        attr_name = f"_{k}"        # Convert to private attribute name
        setattr(self, attr_name, v) # Set attribute, e.g., self._dump_all = v
    else:
        raise KeyError(f"Unknown parameter: {k}")
```

**Example**:
```python
# Method call
obj.config(dump_all=True, include=["data"], exclude=["_cache"])

# Internal execution
# k="dump_all", v=True → attr_name="_dump_all", setattr(self, "_dump_all", True)
# k="include", v=["data"] → attr_name="_include", setattr(self, "_include", ["data"])
# k="exclude", v=["_cache"] → attr_name="_exclude", setattr(self, "_exclude", ["_cache"])
```

#### 2. Recursive Processing of Child Objects

```python
if recursive:
    for obj in self.__dict__.values():
        # Set a flag to prevent infinite loops
        self.__dict__[self.FLAG_KEY] = True
        
        # If the child object is Serializable and hasn't been processed yet
        if isinstance(obj, Serializable) and self.FLAG_KEY not in obj.__dict__:
            obj.config(recursive=True, **kwargs)  # Recursive call
            
        # Clean up the flag
        del self.__dict__[self.FLAG_KEY]
```

### Complete Example

```python
class MyModel(Serializable):
    def __init__(self):
        super().__init__()
        self.data = [1, 2, 3]
        self.params = {"lr": 0.01}
        self._cache = {"temp": 123}
        self.sub_model = MySubModel()  # Another Serializable object

class MySubModel(Serializable):
    def __init__(self):
        super().__init__()
        self.weights = [0.1, 0.2]
        self._temp = "should not save"

# Create the main object
model = MyModel()

# Configure serialization rules
model.config(
    recursive=True,              # Apply recursively to sub_model
    dump_all=False,              # Do not save private attributes
    include=["data", "params"],  # Explicitly save these attributes
    exclude=["_cache"]            # Explicitly exclude this attribute
)

# After configuration:
# - model.data → saved (in include list)
# - model.params → saved (in include list)
# - model._cache → not saved (in exclude list)
# - model.sub_model.weights → saved (due to recursion and not excluded)
# - model.sub_model._temp → not saved (private attribute with dump_all=False)
```

### Why is `FLAG_KEY` Needed?

It prevents infinite recursion loops, especially when objects reference each other cyclically:

```python
class Node(Serializable):
    def __init__(self):
        self.child = None
        self.parent = None

# Create a circular reference
a = Node()
b = Node()
a.child = b
b.parent = a

# Without FLAG_KEY, recursive configuration would cause:
a.config(recursive=True)
# a → b → a → b → ... Infinite loop!

# With FLAG_KEY:
a.config(recursive=True)
# a sets flag, processes a
# Encounter a.child = b, b has no flag, processes b
# b sets flag, processes b
# Encounter b.parent = a, a already has flag, skip
# Recursion ends safely
```

### Summary

| Feature | Description |
|---------|-------------|
| **Set Rules** | Control serialization behavior via `dump_all`, `include`, and `exclude` parameters |
| **Recursive Application** | When `recursive=True`, automatically applies configuration to all `Serializable` child objects |
| **Cycle Prevention** | Uses `FLAG_KEY` to mark already processed objects, avoiding infinite recursion |
