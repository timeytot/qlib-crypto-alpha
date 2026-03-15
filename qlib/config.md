# Understanding Qlib's Configuration System: `C` (Global Config) and `config_c`

This document explains the structure of Qlib's global configuration object `C` and the temporary configuration object `config_c`, as used in methods like `register_from_C`.

## Reference Implementation

The code discussed in this document can be found in the Qlib repository:
- [qlib/config.py#L108](https://github.com/microsoft/qlib/blob/main/qlib/config.py#L108) - `QlibConfig` class and global `C` instance

## 1. Structure of `C` - The Global Configuration Object

`C` is the **global singleton instance** of the `QlibConfig` class, created at the end of the configuration file. It holds the master settings for the entire Qlib framework.

```python
# Global configuration instance
C = QlibConfig(_default_config)
```

### Internal Structure of `C`

The `C` object is an instance of `QlibConfig`, which inherits from `Config`. Its core data is stored in the `_config` dictionary.

```python
C = QlibConfig(
    # Core configuration dictionary - the actual settings
    _config = {
        # ---------- Data Provider Configuration ----------
        "calendar_provider": "LocalCalendarProvider",
        "instrument_provider": "LocalInstrumentProvider",
        "feature_provider": "LocalFeatureProvider",
        "pit_provider": "LocalPITProvider",
        "expression_provider": "LocalExpressionProvider",
        "dataset_provider": "LocalDatasetProvider",
        "provider": "LocalProvider",
        
        # ---------- Data Path ----------
        "provider_uri": "",               # Path to the data storage (can be a dict for multi-frequency)
        
        # ---------- Cache Configuration ----------
        "expression_cache": None,          # Cache for expressions (e.g., "DiskExpressionCache")
        "calendar_cache": None,
        "dataset_cache": None,              # Cache for datasets (e.g., "DiskDatasetCache")
        "local_cache_path": None,           # Path for local cache files
        
        # ---------- Parallel Processing ----------
        "kernels": 8,                       # Number of CPU cores to use (NUM_USABLE_CPU)
        "maxtasksperchild": None,            # Max tasks per child process in parallel
        "joblib_backend": "multiprocessing", # Backend for joblib parallel execution
        
        # ---------- Logging Configuration ----------
        "logging_level": 20,                 # logging.INFO
        "logging_config": {                   # Detailed logging config dictionary
            "version": 1,
            "formatters": {...},
            "handlers": {...},
            "loggers": {...}
        },
        
        # ---------- Redis Configuration ----------
        "redis_host": "127.0.0.1",
        "redis_port": 6379,
        "redis_task_db": 1,
        "redis_password": None,
        
        # ---------- Memory Cache ----------
        "mem_cache_size_limit": 500,
        "mem_cache_expire": 3600,            # 1 hour
        
        # ---------- Experiment Management ----------
        "exp_manager": {
            "class": "MLflowExpManager",
            "module_path": "qlib.workflow.expm",
            "kwargs": {...}
        },
        
        # ---------- PIT (Point-in-Time) Configuration ----------
        "pit_record_type": {...},
        "pit_record_nan": {...},
        
        # ---------- Other Configurations ----------
        "region": "cn",                       # Default region (REG_CN)
        "min_data_shift": 0,
        # ... and more
    },
    
    # Additional attributes (not in _config)
    _registered = False,                      # Flag indicating if components are registered
    _default_config = {...}                   # Deep copy of the original default config for reset
)
```

**Key points about `C`**:
- It's a **singleton**; all parts of Qlib import and use this same instance.
- Settings are accessed via dictionary-like syntax (`C["provider_uri"]`) or attribute syntax (`C.provider_uri`).
- It includes the `_registered` flag to track whether core components (ops, data wrappers, etc.) have been initialized.

## 2. Structure of `config_c` - The Passed-in Configuration Object

`config_c` is **another instance** of `QlibConfig` (or its base class `Config`). It is typically created temporarily to hold new configuration values that need to be merged into the global `C`.

### Creation Examples

```python
# Example 1: Create an empty config and set its mode
client_config = QlibConfig({})          # Create with empty default
client_config.set_mode("client")         # Apply client-specific settings from MODE_CONF

# Example 2: Create a config with specific overrides
custom_config = QlibConfig({
    "provider_uri": "/custom/data/path",
    "kernels": 16,
    "region": "us"
})

# Example 3: A config object might be created internally by qlib.init()
```

### Internal Structure of `config_c`

`config_c` has the **exact same class structure** as `C`, but its `_config` dictionary typically contains only a **subset of settings** intended to update the global ones.

```python
config_c = QlibConfig(
    _config = {
        # Only the settings that need to be updated or are specific to a mode
        "provider_uri": "/new/data/path",     # New data path
        "kernels": 32,                         # New number of kernels
        "region": "us",                         # New region
        "logging_level": 10,                    # DEBUG level
        "dataset_cache": "DiskDatasetCache",     # Enable dataset cache
        # ... other updated configurations
    },
    
    # Other attributes (may not be relevant for the update)
    _registered = False,
    _default_config = {...}
)
```

**Key points about `config_c`**:
- It is a **temporary container** for new configuration values.
- It is passed to methods like `C.register_from_C(config_c)`.
- Its `_config` dictionary is merged into `C`'s `_config` using `C.update()`.

## 3. Complete Example: How `config_c` Updates `C`

This example illustrates the process of updating the global configuration using a temporary config object.

```python
# 1. Initial state - Default global config
C._config = {
    "provider_uri": "",
    "kernels": 8,
    "region": "cn",
    "logging_level": 20,           # INFO
    "dataset_cache": None,
    # ... other settings
}
C._registered = False

# 2. Create a new configuration object with desired updates
new_config = QlibConfig({})        # Create a new instance
new_config._config = {              # Directly set its _config (simplified)
    "provider_uri": "/mnt/data/qlib",
    "kernels": 32,
    "region": "us",
    "dataset_cache": "DiskDatasetCache"
    # Note: "logging_level" is not included, so it will remain unchanged
}

# 3. Call register_from_C to merge and register
C.register_from_C(new_config)

# What happens inside register_from_C:
#
# a. Check registration:
#    if C.registered and skip_register: ...  # C._registered=False, so proceed
#
# b. Merge configurations via set_conf_from_C:
#    C.set_conf_from_C(new_config)
#    -> self.update(**new_config.__dict__["_config"])
#    -> C.update(provider_uri="/mnt/data/qlib", kernels=32, region="us", dataset_cache="DiskDatasetCache")
#
# c. Update logging if config changed:
#    if C.logging_config: set_log_with_config(C.logging_config)  # Runs if logging_config exists
#
# d. Register all components:
#    C.register()  # Registers ops, data wrappers, experiment manager
#    -> C._registered = True

# 4. Resulting state of C after the call
C._config = {
    "provider_uri": "/mnt/data/qlib",       # Updated
    "kernels": 32,                           # Updated
    "region": "us",                          # Updated
    "logging_level": 20,                      # Unchanged (not in new_config)
    "dataset_cache": "DiskDatasetCache",      # Updated
    # ... other settings remain the same
}
C._registered = True                         # Now registered
```

## Summary of Differences and Relationships

| Feature | `C` (Global Config) | `config_c` (Passed-in Config) |
| :--- | :--- | :--- |
| **Type** | Singleton instance of `QlibConfig` | Another instance of `QlibConfig` |
| **Scope** | Global, used by all Qlib modules | Temporary, created for a specific update |
| **Persistence** | Exists for the lifetime of the Qlib session | Typically discarded after the update |
| **Content** | Contains the **full, current** configuration | Contains a **subset** of new/overriding values |
| **Role** | The source of truth for all settings | A vehicle to deliver updates to `C` |
| **Registered Flag**| `_registered` indicates if core components are initialized | `_registered` is usually `False` and irrelevant |

The core mechanism is that `register_from_C` takes a temporary configuration object (`config_c`), merges its settings into the permanent global object (`C`), and then triggers the necessary registration steps to apply those settings across the framework. This pattern allows for flexible and centralized configuration management.
