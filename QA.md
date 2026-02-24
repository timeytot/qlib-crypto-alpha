# Resolving MLflow Filesystem Tracking Deprecation Warning in Qlib

**Code References:**
- [`qlib/workflow/__init__.py`](https://github.com/microsoft/qlib/blob/main/qlib/workflow/__init__.py)
- [`qlib/workflow/expm.py`](https://github.com/microsoft/qlib/blob/main/qlib/workflow/expm.py)

## Problem

When using Qlib's workflow with default MLflow settings, you may encounter this warning:

```
C:\Users\...\mlflow\tracking\_tracking_service\utils.py:140: FutureWarning: Filesystem tracking backend (e.g., './mlruns') is deprecated...
```

**What it means:** You're using the default local `./mlruns` folder for experiment tracking. MLflow is moving toward recommending database backends (e.g., SQLite), but local file storage still works perfectly fine for now.

## Solution

### Option 1: Configure in `qlib.init()`

Pass an `exp_manager` configuration to use SQLite backend:

```python
qlib.init(
    provider_uri=provider_uri,
    region=REG_CN,
    exp_manager={
        "class": "MLflowExpManager",
        "module_path": "qlib.workflow.expm",
        "kwargs": {
            "uri": "sqlite:///mlflow.db",        # Use SQLite instead of filesystem
            "default_exp_name": "Experiment"  
        }
    }
)
```

### Option 2: Configure when starting a run

Specify the `uri` directly in the `R.start()` context manager:

```python
from qlib.workflow import R

with R.start(
    experiment_name="train_model", 
    uri="sqlite:///mlflow.db"                    # URI only used in qlib.workflow modules
):
    R.log_params(**flatten_dict(task))
    model.fit(dataset)
    R.save_objects(trained_model=model)
    rid = R.get_recorder().id
```

**Note:** The `uri` parameter is specifically used in [`qlib/workflow/__init__.py`](https://github.com/microsoft/qlib/blob/main/qlib/workflow/__init__.py) and [`qlib/workflow/expm.py`](https://github.com/microsoft/qlib/blob/main/qlib/workflow/expm.py).

### Option 3: Keep using filesystem (ignore warning)

If you prefer to keep using the local filesystem and just suppress the warning:

```python
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="mlflow.tracking._tracking_service.utils")
```

## Why This Happens

MLflow is gradually phasing out filesystem-based tracking backends in favor of database backends (SQLite, MySQL, PostgreSQL) for better performance, reliability, and concurrent access support. The warning alerts users to this upcoming change.

## Summary

The warning is harmless for now — your existing `./mlruns` setup will continue working. To future-proof your code, switch to SQLite using either configuration method above.
