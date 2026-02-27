# Qlib AsyncCaller & Recorder Logging Mechanism

## Reference Links
- [recorder.py#L445](https://github.com/microsoft/qlib/blob/main/qlib/workflow/recorder.py#L445)
- [paral.py#L72](https://github.com/microsoft/qlib/blob/main/qlib/utils/paral.py#L72)

## Understanding the AsyncCaller and Recorder Logging Flow

This document explains how Qlib's asynchronous logging works, from class definition to method invocation, with special focus on how `functools.partial` bridges the main thread and background worker.

### Stage 1: Class Definition Time (Executed Once During Module Import)

```python
class MLflowRecorder(Recorder):

    @AsyncCaller.async_dec(ac_attr="async_log")
    def log_params(self, **kwargs):
        # Original implementation (will be replaced)
        mlflow.log_params(**kwargs)
```

**What happens here?** (Executed once when the class is defined)

1. Python sees `@AsyncCaller.async_dec(ac_attr="async_log")`

2. **Calls the decorator factory function**:
   ```python
   # This line is NOT written by the user - it's what Python does internally
   decorator_func = AsyncCaller.async_dec(ac_attr="async_log")
   ```
   - `async_dec` is a **staticmethod** that acts as a **factory function**
   - It receives the argument `ac_attr="async_log"`
   - Inside `async_dec`, it defines and **returns the inner `decorator_func`**
   - The returned `decorator_func` is a closure that remembers the `ac_attr` value

   ```python
   @staticmethod
   def async_dec(ac_attr):              # ← Factory function called with "async_log"
       def decorator_func(func):         # ← This is the inner decorator being returned
           def wrapper(self, *args, **kwargs):
               # ... wrapper logic ...
           return wrapper
       return decorator_func             # ← Returns the inner decorator_func
   ```

3. **Python passes the original `log_params` function to `decorator_func`**:
   ```python
   # Again, this is Python's internal mechanism
   log_params = decorator_func(original_log_params)
   ```
   - `decorator_func` receives the original `log_params` function as its `func` parameter
   - Inside `decorator_func`, it defines and returns the `wrapper` function
   
   ```python
   def decorator_func(func):         # ← This is the inner decorator being returned
       def wrapper(self, *args, **kwargs):
           # ... wrapper logic ...
       return wrapper                # ← Returns the wrapper function
   ```
   
   - The `wrapper` is a closure that:
     - Remembers the original `log_params` function (via the `func` parameter from the outer scope)
     - Remembers the `ac_attr` value (via closure from `async_dec`)

4. **Result**:
   ```python
   # The class's log_params is now the wrapper function
   # log_params ← wrapper
   ```
   - The name `log_params` in the class now points to the `wrapper` function
   
   - This `wrapper` is a closure that:
     - Has access to the original `log_params` function (via the `func` parameter from `decorator_func`)
     - Has access to the `ac_attr="async_log"` parameter (via closure from `async_dec`)
   
   - When called later, the `wrapper` will execute this logic:
     ```python
     # Inside the wrapper at runtime
     if callable(caller):  # if self.async_log exists and is callable
         return getattr(self, ac_attr)(func, self, *args, **kwargs)  # Async path
     else:
         return func(self, *args, **kwargs)  # Sync fallback path
     ```
     Where:
     - `getattr(self, ac_attr)` retrieves the `AsyncCaller` instance
     - `func` is the original `log_params` function
     - `self, *args, **kwargs` are the actual runtime arguments

### Stage 2: Instance Creation + Setting AsyncCaller in start_run

```python
class MLflowRecorder(Recorder):

    def start_run(self):
        # ... other code ...
        
        # Critical step: create the async caller here
        self.async_log = AsyncCaller()           # ← Background thread starts, listening to queue
        
        # ... subsequent code ...
```

- `self.async_log` is only assigned when the experiment officially starts
- Calling `log_params` before this point will use the synchronous path (since `self.async_log` is `None`)

### Stage 3: Runtime - What Actually Executes

When `recorder.log_params(learning_rate=0.01, batch_size=32)` is called later, this is the code that runs:

```python
# Simplified wrapper logic with partial explanation
def wrapper(self, *args, **kwargs):
    caller = getattr(self, "async_log", None)          # → AsyncCaller instance (normal case)
    
    if callable(caller):
        # Key: use partial to package "original log_params + all current parameters" 
        # into a "delay-executable task"
        task = partial(original_log_params_func, self, *args, **kwargs)
        # task is now a callable object; calling task() is equivalent to:
        #   original_log_params_func(self, learning_rate=0.01, batch_size=32)
        
        # Put this task into the queue via AsyncCaller.__call__
        caller(task)  # This calls AsyncCaller.__call__(task)
        # The __call__ method does: self._q.put(partial(func, *args, **kwargs))
        # Which puts the task into the internal queue for background processing
        
        # Alternative equivalent form (if called with original function + args):
        # caller(original_log_params_func, self, *args, **kwargs) 
        # → This also ends up creating a partial and putting it in the queue
        
        return None  # Returns immediately, doesn't wait for execution
    else:
        # Synchronous fallback
        return func(self, *args, **kwargs)
```

### Inside AsyncCaller.__call__

```python
def __call__(self, func, *args, **kwargs):
    # func can be either:
    #   - A partial object (already packaged task)
    #   - The original function (with separate args)
    
    # Package into a partial if not already done
    task = partial(func, *args, **kwargs)
    
    # Put the task into the queue
    self._q.put(task)  # ← The queue is where tasks wait for background processing
    
    # Returns immediately - background thread will pick up and execute later
```

### The Queue's Role

- **Storage**: The queue (`self._q`) acts as a FIFO buffer holding pending tasks
- **Thread-safe**: Queue implementation ensures safe concurrent access
- **Bounded**: Can be configured with max size to prevent memory issues
- **Background consumption**: The AsyncCaller's background thread continuously takes tasks from this queue and executes them

### What `partial` Captures - Detailed Breakdown

| Element | Example Value (this call) | Description |
|---------|---------------------------|-------------|
| First arg to partial | Original `log_params` function | The actual function to execute later |
| Positional args after func | `self` (the recorder instance) | Instance method needs `self` |
| `**kwargs` | `{"learning_rate": 0.01, "batch_size": 32}` | All keyword args passed by user |
| Final `task` object | `partial(original_log_params, recorder, learning_rate=0.01, batch_size=32)` | Calling `task()` = `original_log_params(recorder, learning_rate=0.01, batch_size=32)` |

**Why `partial` is crucial**:
- Freezes function + arguments into a "ready-to-call" object
- Background thread just needs to execute `task()` to reproduce the exact `log_params` call
- Ensures parameter consistency in async execution
- No need to store strings or serialize complex objects in the queue
