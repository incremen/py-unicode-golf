"""Test the reversed(range(n+1)) approach — no uncalled function refs."""

from core.anchors import build_n
import time

# Step 1: Verify the concept
print("=== Verify reversed(range(n+1)) trick ===")
print(f"next(zip(reversed(range(113)), reversed(range(122)))) = {next(zip(reversed(range(113)), reversed(range(122))))}")
# Should be (112, 121) = bytes for 'p', 'y'
print(f"bytes(...) = {bytes(next(zip(reversed(range(113)), reversed(range(122)))))}")
print(f"eval(...) = {eval(bytes(next(zip(reversed(range(40)), reversed(range(113)), reversed(range(122)), reversed(range(40))))))}")
print()

# Step 2: Build with builtin-only expressions
def build_string_reversed(text):
    """Build string using reversed(range(b+1)) iterators — no uncalled refs."""
    if len(text) == 1:
        from core.anchors import build_char
        return build_char(text)

    repr_bytes = repr(text).encode('utf-8')
    # For each byte b, we need reversed(range(build_n(b+1)))
    # The first element of reversed(range(b+1)) is exactly b
    rev_exprs = [f'reversed(range({build_n(b + 1)}))' for b in repr_bytes]
    return f'eval(bytes(next(zip({",".join(rev_exprs)}))))'

print("=== Test generated expressions ===")
tests = ["A", "hi", "py", "abc", "hello", "hello world", "ඞ"]

for t in tests:
    expr = build_string_reversed(t)
    start = time.time()
    try:
        res = eval(expr)
        elapsed = time.time() - start
        status = "OK" if res == t else f"FAIL (got {res!r})"
        print(f"  {len(t):>3} chars | {status} | expr_len={len(expr):>5} | eval={elapsed:.4f}s")
    except Exception as e:
        print(f"  {len(t):>3} chars | ERROR: {e}")

print()

# Compare with old chr/map/ord approach
def build_string_old(text):
    repr_bytes = repr(text).encode('utf-8')
    chr_exprs = [f'chr({build_n(b)})' for b in repr_bytes]
    return f'eval(bytes(map(ord,next(zip({",".join(chr_exprs)})))))'

print("=== Compare: reversed(range) vs chr/map/ord ===")
for t in ["hi", "hello", "hello world"]:
    expr_new = build_string_reversed(t)
    expr_old = build_string_old(t)
    print(f"  {t!r:15s} | new={len(expr_new):>5} | old={len(expr_old):>5} | diff={len(expr_new)-len(expr_old):+d}")
