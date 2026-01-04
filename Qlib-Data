https://github.com/microsoft/qlib/blob/main/qlib/data/data.py#L1331  register_wrapper(D, C.provider, "qlib.data")
https://github.com/microsoft/qlib/blob/main/qlib/config.py#L142  "provider": "LocalProvider",
https://github.com/microsoft/qlib/blob/main/qlib/utils/__init__.py#L865  self._provider = provider
  Core Mechanism: Wrapper + register_wrapperThe Wrapper class is a proxy/delegate pattern implementation. Its sole purpose is to delay the actual instantiation of providers until qlib.init() is called, while allowing users to call methods (like D.features(), D.instruments()) directly on the wrapper object as if it were the real provider.python
  
  class Wrapper:
      def __init__(self):
          self._provider = None
  
      def register(self, provider):
          self._provider = provider   # ← Here: assign the real instance
  
      def __getattr__(self, key):
          if self._provider is None:
              raise AttributeError("Please run qlib.init() first")
          return getattr(self._provider, key)  # ← Delegate all calls to the real provider
  
  What does register_wrapper(D, C.provider, "qlib.data") do?In register_all_wrappers(C):python
  
  register_wrapper(D, C.provider, "qlib.data")
  
  This line does the following:C.provider is a config (e.g., "LocalProvider" or a full config dict).
  init_instance_by_config(C.provider, ...) creates the actual instance (e.g., a LocalProvider() object).
  register_wrapper(...) calls D.register(that_instance), which executes:python
  
  D._provider = local_provider_instance
  
  Result: What is D after qlib.init()?D is an instance of Wrapper.
  It has all the methods of BaseProvider (e.g., .features(), .instruments(), .calendar(), etc.) because LocalProvider inherits from BaseProvider.
  When you call D.features(...), it actually forwards the call to D._provider.features(...) via __getattr__.
  
  So yes:D itself is a Wrapper, but behaves exactly like a BaseProvider because all method calls are delegated to the real provider instance stored in D._provider.
  
  In a nutshell:
  BaseProvider in the type hint is purely for static type checking and IDE support.
  It tells tools like mypy, PyCharm, or VS Code:  "Even though the object is a Wrapper, you can safely assume it has all the methods and behavior of BaseProvider (e.g., .features(), .instruments(), .calendar())."
  At runtime, this type annotation has zero effect — Python ignores Annotated completely during execution.
  The actual object at runtime is always an instance of Wrapper.  python
  
  D = Wrapper()                  # ← Real object in memory
  isinstance(D, Wrapper)         # → True
  isinstance(D, BaseProvider)    # → False (it's not a subclass)
  
  The real functionality comes from D._provider.
  After qlib.init():python
  
  D._provider = LocalProvider() (or ClientProvider, etc.)
  
  This _provider is a concrete subclass of BaseProvider, so it implements all the actual methods.When you call:python
  
  D.features(...)
  
  → Wrapper.__getattr__ forwards it to:python
  
  D._provider.features(...)
  
  SummaryAspect
  What it is
  Runtime impact?
  Type hint
  Annotated[BaseProvider, Wrapper]
  None (only for static analysis)
  Actual object
  Wrapper() instance
  Yes — this is what exists
  Real implementation
  D._provider (e.g., LocalProvider() instance)
  Yes — this does the real work
  
  Conclusion in one sentence:
  BaseProvider in the annotation is just a type hint for better developer experience (autocomplete, error checking) and has no runtime effect. The real object is a Wrapper, and the actual BaseProvider functionality lives in the delegated _provider instance.
  
