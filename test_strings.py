"""Test the int.to_bytes().decode() approach for encoding strings."""

from core.anchors import build_n

# First: does the concept work at all?
print("=== Concept test (manual) ===")
n = int.from_bytes(b"hi", 'big')  # 26729
print(f"'hi' as int: {n}")
print(f"Roundtrip: {n.to_bytes(2).decode()!r}")
print()

# Test with single chars and very short strings (small ints)
tests = ["A", "hi", "abc", "abcd", "abcde", "acdef"]

for t in tests:
    utf8 = t.encode('utf-8')
    n = int.from_bytes(utf8, 'big')
    length = len(utf8)
    print(f"{t!r}: n={n}, length={length}")

    expr_n = build_n(n)
    expr_l = build_n(length)
    expr = f"({expr_n}).to_bytes({expr_l}).decode()"

    result = eval(expr)
    status = "OK" if result == t else f"FAIL (got {result!r})"
    print(f"  {status}, expr len={len(expr)}")
    print(f"  Expression: {expr}")
    print()
