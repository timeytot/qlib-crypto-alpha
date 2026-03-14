# `DLWParser._parse_fields_info` Method

**Source Code**: https://github.com/microsoft/qlib/blob/main/qlib/data/dataset/loader.py#L95

This document explains the `_parse_fields_info` method, which is the core parsing logic in Qlib's `DLWParser` class. It converts user-friendly field configurations into a standardized `(exprs, names)` tuple format.

## Method Signature

```python
def _parse_fields_info(self, fields_info: Union[list, tuple]) -> Tuple[list, list]:
```

## Parsing Logic

The method handles two common configuration patterns based on the type of the **first element** in `fields_info`.

### Case 1: First Element is a String (Shorthand Form)

```python
if isinstance(fields_info[0], str):
    exprs = names = fields_info
```

**When it's used**: The user provides only a list of expressions, and wants to use the expressions themselves as column names.

**Example**:
```python
fields_info = ["$close", "Ref($close, 1)", "Mean($close, 5)"]

# Parsing result:
exprs = ["$close", "Ref($close, 1)", "Mean($close, 5)"]
names = ["$close", "Ref($close, 1)", "Mean($close, 5)"]  # Column names default to expressions
```

### Case 2: First Element is a List/Tuple (Full Form)

```python
elif isinstance(fields_info[0], (list, tuple)):
    exprs, names = fields_info
```

**When it's used**: The user explicitly provides both expressions and custom column names as a tuple/list pair.

**Example**:
```python
fields_info = (
    ["$close", "Ref($close, 1)"],
    ["CLOSE", "CLOSE_LAG1"]
)

# Parsing result:
exprs = ["$close", "Ref($close, 1)"]
names = ["CLOSE", "CLOSE_LAG1"]  # Custom column names
```

- **Full form**: Explicit expressions and custom column names

This design allows Qlib's data loaders to handle various configuration styles while maintaining a consistent internal representation.
