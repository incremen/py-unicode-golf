"""Test the pure-functional eval(bytes(map(ord, next(zip(...))))) approach."""

import time
from core.anchors import build_n

# Step 1: Verify the pure functional zip trick works natively
print("=== Verify pure functional zip trick ===")

# The target is the string 'py'. Its repr() is "'py'".
# The UTF-8 bytes for "'py'" are 39, 112, 121, 39.
test_zip = next(zip(chr(39), chr(112), chr(121), chr(39)))
print(f"next(zip(...))      = {test_zip}")

test_map = list(map(ord, next(zip(chr(39), chr(112), chr(121), chr(39)))))
print(f"map(ord, ...)       = {test_map}")

# eval() natively accepts bytes in Python 3. No .decode() needed!
result = eval(bytes(map(ord, next(zip(chr(39), chr(112), chr(121), chr(39))))))
print(f"eval(bytes(...))    = {result!r}\n")


# Step 2: Build it using the project's base-3 generator
def build_string_zip(text):
    """Build string strictly using the zip trick + eval, zero literals."""
    # repr() adds the quotes so eval() parses it back as a string
    repr_bytes = repr(text).encode('utf-8')
    
    # Each byte becomes chr(build_n(byte_value))
    chr_exprs = [f'chr({build_n(b)})' for b in repr_bytes]
    zip_args = ','.join(chr_exprs)
    
    # Notice: ZERO brackets, arrays, or syntax grouping.
    return f'eval(bytes(map(ord, next(zip({zip_args})))))'

print("=== Test generated expressions ===")
tests = [
    "A", "hi", "py", "abc", "hello", "hello world",
    "the quick brown fox jumps over the lazy dog","ඞ"
]

for t in tests:
    expr = build_string_zip(t)
    start = time.time()
    try:
        res = eval(expr)
        elapsed = time.time() - start
        status = "OK" if res == t else f"FAIL (got {res!r})"
        print(f"  {len(t):>3} chars | {status} | expr_len={len(expr):>5} | eval={elapsed:.4f}s")
        print(f"    expr: {expr}")
        print("eval(expr) = ", eval(expr))
    except Exception as e:
        print(f"  {len(t):>3} chars | ERROR: {e}")

print()

# Step 3: The Comparison
print("=== Compare: Strict zip+eval vs Cheating bytes([]) ===")
def build_string_list_cheat(text):
    """The lazy approach using forbidden list literals []."""
    utf8 = text.encode('utf-8')
    byte_exprs = [build_n(b) for b in utf8]
    inner = ','.join(byte_exprs)
    return f'bytes([{inner}]).decode()'

for t in ["hi", "hello", "hello world"]:
    expr_zip = build_string_zip(t)
    expr_list = build_string_list_cheat(t)
    diff = len(expr_zip) - len(expr_list)
    print(f"  {t!r:15s} | zip={len(expr_zip):>5} | list={len(expr_list):>5} | diff={diff:+d}")