https://github.com/microsoft/qlib/blob/main/qlib/utils/index_data.py#L332  __get__,self_data_method(other_aligned.data),index_data_ops_creator,class IndexData(metaclass=index_data_ops_creator)
  Python Descriptor-Powered Operator Overloading in index_dataThis note explains how the index_data library (a lightweight, high-performance alternative to Pandas) implements arithmetic and comparison operators (+, -, *, /, ==, >, <, etc.) using Python descriptors, NumPy ufuncs, and a custom metaclass.The design is elegant: all operators share the same implementation, automatically align indices, and perform computations at NumPy speed.1. How s1 + s2 Triggers the MechanismWhen Python encounters s1 + s2:It looks up s1.__add__ to call s1.__add__(s2).
  __add__ is not a regular method — it is a BinaryOps descriptor instance injected into the class by a metaclass.
  Because BinaryOps implements __get__, Python's descriptor protocol kicks in.
  Accessing s1.__add__ automatically calls:python
  
  BinaryOps_instance.__get__(obj=s1, owner=IndexData)
  
  Inside __get__:python
  
  self.obj = s1        # Bind the left operand
  return self          # Return the bound BinaryOps instance (now callable)
  
  Python immediately calls the returned object with the right operand:python
  
  bound_binary_ops(s2)   # → enters BinaryOps.__call__(other=s2)
  
  This is why the left operand (s1) is available inside __call__ as self.obj.Reference: Python Descriptor Guide – https://docs.python.org/3/howto/descriptor.html
  2. Metaclass: Injecting Operators into the ClassThe operators are added dynamically using a metaclass-like function:python
  
  def index_data_ops_creator(*args, **kwargs):
      for method_name in ["__add__", "__sub__", "__rsub__", "__mul__", 
                          "__truediv__", "__eq__", "__gt__", "__lt__"]:
          args[2][method_name] = BinaryOps(method_name=method_name)
      return type(*args)
  
  class IndexData(metaclass=index_data_ops_creator):
      ...
  
  When Python creates the class, it calls:python
  
  index_data_ops_creator('IndexData', (object,), class_dict)
  
  The *args tuple contains the standard three arguments passed to a metaclass:Index
  Name
  Content Example
  Purpose
  0
  name
  'IndexData'
  Class name
  1
  bases
  (object,)
  Base classes
  2
  dict
  {'loc': ..., 'sum': ..., ...}
  Class namespace (attributes)
  
  The function modifies args[2] (the class dictionary) by inserting a BinaryOps instance for each special method, then returns type(*args) to create the final class.Result: All subclasses of IndexData (SingleData, MultiData) automatically support the operators.3. Inside BinaryOps.__call__ – The Real Computationpython
  
  def __call__(self, other):
      # self.obj is the left operand (s1), bound during __get__
      self_data_method = getattr(self.obj.data, self.method_name)  # e.g., np.add
  
      if isinstance(other, (int, float, np.number)):
          result_data = self_data_method(other)                    # scalar op
      elif isinstance(other, self.obj.__class__):
          other_aligned = self.obj._align_indices(other)            # align indices
          result_data = self_data_method(other_aligned.data)       # vectorized op
      else:
          return NotImplemented
  
      return self.obj.__class__(result_data, *self.obj.indices)
  
  Key DetailsWhy self_data_method is a NumPy ufuncpython
  
  self_data_method = getattr(self.obj.data, "__add__")  # → np.add
  
  self.obj.data is a np.ndarray
  NumPy arrays implement special methods (__add__, __sub__, etc.) that return bound ufuncs
  So self_data_method is exactly np.add, np.subtract, etc.
  
  Why self_data_method(other_aligned.data) works without writing self.obj.dataNumPy ufuncs obtained via getattr(array, "__add__") are partially bound to the original array.python
  
  add_func = arr1.__add__        # bound version of np.add
  add_func(arr2)                 # → internally calls np.add(arr1, arr2)
  
  Thus:python
  
  self_data_method(other_aligned.data)
  # Equivalent to:
  np.add(self.obj.data, other_aligned.data)
  
  This is a NumPy idiom that saves writing the left operand twice.*self.obj.indices – Unpacking Indicesself.obj.indices is a list of Index objects:SingleData: [row_index]
  MultiData: [row_index, column_index]
  
  The star unpacks it to match the constructor signature:python
  
  SingleData(result_data, self.obj.indices[0])
  # or
  MultiData(result_data, row_index, column_index)
  
  This preserves the original indices (aligned to the left operand, just like Pandas).SummaryDescriptors (__get__) bind the left operand dynamically when the operator is accessed.
  A metaclass function injects the same BinaryOps descriptor for all operators.
  NumPy ufuncs provide blazing-fast vectorized computation.
  The result is recreated with the left operand’s class and indices, ensuring consistent alignment behavior.
  
  This pattern combines Python’s descriptor protocol with NumPy’s performance — a clean, reusable, and extremely efficient way to implement operator overloading for array-like objects.

