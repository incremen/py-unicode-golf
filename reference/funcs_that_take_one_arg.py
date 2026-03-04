import inspect
import builtins

# Filter for functions that can take exactly 1 positional argument
single_input_builtins = []

for name in dir(builtins):
    obj = getattr(builtins, name)
    if callable(obj):
        try:
            sig = inspect.signature(obj)
            # Check if 1 argument is valid according to the signature
            sig.bind(1) 
            single_input_builtins.append(name)
        except (ValueError, TypeError):
            # Some built-ins (like range) are C-defined and have no signature
            # but we know they take 1 arg.
            continue

print(f"Found {len(single_input_builtins)} built-ins that accept one input.")
print(single_input_builtins)