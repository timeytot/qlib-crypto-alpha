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
