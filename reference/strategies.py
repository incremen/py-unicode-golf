"""All known strategies for constructing integers from single-arg Python builtins.

Each strategy is documented with:
  - The expression template
  - Exact formula
  - Paren cost (number of opening parens added)
  - Constraints (if any)
"""


# =============================================================================
# SEEDS (zero-arg constructors → integers)
# =============================================================================
# These produce integers with no input, serving as recursion base cases.
#
# See BASE_ANCHORS in anchors.py for the full set (0-125).
# Key ones:
#   int(not())       = 1   (2 parens)
#   len(str(not()))   = 4   (3 parens)
#   ord(min(str(not()))) = 84  (4 parens)
#   ord(max(str(dict()))) = 125 (4 parens)


# =============================================================================
# DECREMENT
# =============================================================================
# max(range(n)) = n - 1
#
# Formula:  f(n) = n - 1
# Parens:   2 per step
# Domain:   n >= 1

def decrement(expr, times=1):
    for _ in range(times):
        expr = f'max(range({expr}))'
    return expr


# =============================================================================
# EXACT 3x MULTIPLIER
# =============================================================================
# len(str(list(bytes(n)))) = 3n
#
# How: bytes(n) → n zero bytes → list → [0, 0, ..., 0] → str → "[0, 0, ..., 0]"
#      Each element contributes exactly 3 chars: "0, " (last one gets "]" instead)
#
# Formula:  f(n) = 3n
# Parens:   4
# Domain:   n >= 1

def triple(expr):
    return f'len(str(list(bytes({expr}))))'


# =============================================================================
# EXACT 4x MULTIPLIER (plus offset)
# =============================================================================
# len(str(bytes(n))) = 4n + 3
#
# How: bytes(n) → n zero bytes → str → "b'\x00\x00...'"
#      Prefix "b'" (2) + suffix "'" (1) = 3 fixed chars.
#      Each \x00 is 4 literal characters in the repr.
#
# Formula:  f(n) = 4n + 3
# Parens:   3
# Domain:   n >= 0

def quad_plus_3(expr):
    return f'len(str(bytes({expr})))'


# =============================================================================
# EXACT 5x MULTIPLIER (plus offset)
# =============================================================================
# len(ascii(str(bytes(n)))) = 5n + 5
#
# How: str(bytes(n)) gives "b'\x00...'". ascii() escapes backslashes and adds
#      outer quotes: "\"b'\\x00...'\"". Each \x00 (4 chars) → \\x00 (5 chars).
#
# Formula:  f(n) = 5n + 5
# Parens:   4
# Domain:   n >= 0

def quint_plus_5(expr):
    return f'len(ascii(str(bytes({expr}))))'


# =============================================================================
# ZIP CHAIN (exact 3(k+1)·n multipliers)
# =============================================================================
# len(str(list(zip^k(bytes(n))))) = 3(k+1)·n
#
# How: Each zip() wrapping turns each element into a deeper tuple.
#      bytes(n)       → [0, 0, ...]           → str len = 3n   (k=0)
#      zip(bytes(n))  → [(0,), (0,), ...]     → str len = 6n   (k=1)
#      zip(zip(...))  → [((0,),), ...]        → str len = 9n   (k=2)
#
# Formula:  f(n) = 3(k+1)·n
# Parens:   4 + k  (len, str, list, bytes, plus k zips)
# Domain:   n >= 1
#
# Useful multipliers:
#   k=0:  3n  (4 parens) — same as triple()
#   k=1:  6n  (5 parens)
#   k=2:  9n  (6 parens)
#   k=3: 12n  (7 parens)
#   k=4: 15n  (8 parens)

def zip_chain(expr, k=1):
    inner = f'bytes({expr})'
    for _ in range(k):
        inner = f'zip({inner})'
    return f'len(str(list({inner})))'


# =============================================================================
# ASCII EXPONENTIAL ENGINE (exact (2^k+3)·n + (2^(k+1)+1) )
# =============================================================================
# len(ascii^k(str(bytes(n)))) = (2^k + 3)·n + (2^(k+1) + 1)
#
# How: str(bytes(n)) contains backslash escapes. Each ascii() call escapes
#      the backslashes again, roughly doubling them. The multiplier on n
#      follows 2^k + 3 (starts at 5 for k=1, then 7, 11, 19, 35, 67, ...).
#
# Formula:  f(n) = (2^k + 3)·n + (2^(k+1) + 1)
# Parens:   2 + k  (len is NOT included — add 1 for len())
#           Total with len: 3 + k
# Domain:   n >= 0
#
# Multiplier table:
#   k=1:    5n +   5  (4 parens total)
#   k=2:    7n +   9  (5 parens)
#   k=3:   11n +  17  (6 parens)
#   k=4:   19n +  33  (7 parens)
#   k=5:   35n +  65  (8 parens)
#   k=6:   67n + 129  (9 parens)
#   k=10: 1027n + 2049 (13 parens)

def ascii_exp(expr, k=1):
    inner = f'str(bytes({expr}))'
    for _ in range(k):
        inner = f'ascii({inner})'
    return f'len({inner})'


# =============================================================================
# TRIANGULAR JUMP (quadratic)
# =============================================================================
# sum(range(n)) = n·(n-1)/2
#
# Formula:  f(n) = n·(n-1)/2
# Parens:   2
# Domain:   n >= 0
#
# Useful for rapid initial scaling from small seeds, but the quadratic
# growth makes it hard to land precisely on targets.

def triangular(expr):
    return f'sum(range({expr}))'


# =============================================================================
# TUPLE VARIANT (3n, except 4 at n=1)
# =============================================================================
# len(str(tuple(bytes(n))))
#
# How: Same as list version but tuple(bytes(1)) → "(0,)" which is len 4.
#      For n >= 2, identical to list: 3n.
#
# Formula:  f(1) = 4,  f(n) = 3n for n >= 2
# Parens:   4
# Domain:   n >= 1
#
# Minor: gives a free +1 at n=1 without needing a decrement.

def triple_tuple(expr):
    return f'len(str(tuple(bytes({expr}))))'


# =============================================================================
# SUMMARY — parens per multiplication factor
# =============================================================================
#
#   Factor  |  Parens  |  Strategy
#   --------|----------|-----------------------------------
#      -1   |    2     |  max(range(n))
#      3x   |    4     |  len(str(list(bytes(n))))
#     4n+3  |    3     |  len(str(bytes(n)))
#     5n+5  |    4     |  len(ascii(str(bytes(n))))
#      6x   |    5     |  len(str(list(zip(bytes(n)))))
#     7n+9  |    5     |  len(ascii(ascii(str(bytes(n)))))
#      9x   |    6     |  len(str(list(zip(zip(bytes(n))))))
#    11n+17 |    6     |  len(ascii^3(str(bytes(n))))
#     12x   |    7     |  len(str(list(zip(zip(zip(bytes(n)))))))
#    19n+33 |    7     |  len(ascii^4(str(bytes(n))))
#    n²/2   |    2     |  sum(range(n))
#
# The ascii exponential gives the best paren-to-multiplier ratio for
# reaching large numbers. The zip chain gives exact clean multipliers.
# The current build algorithm uses base-3 (triple + decrement) which
# gives 100% Unicode coverage at max depth 114.


# =============================================================================
# DICT ENUMERATOR (exact 6n for small n)
# =============================================================================
# len(str(dict(enumerate(bytearray(n))))) = 6n   (for n < 10)
#
# How: bytearray(n) → n zeroes. enumerate() pairs with indices:
#      (0,0), (1,0), ... dict() → {0: 0, 1: 0, ...}
#      str → "{0: 0, 1: 0, ...}" — each entry is 6 chars.
#
# Formula:  f(n) = 6n          (n < 10, single-digit indices)
#           grows faster for n >= 10 as indices gain digits
# Parens:   5
# Domain:   n >= 1
#
# Same multiplier as zip chain k=1, but with dict repr instead of tuples.
# Breaks exactness at n=10 when indices become 2 digits.

def dict_enum(expr):
    return f'len(str(dict(enumerate(bytearray({expr})))))'


# =============================================================================
# SUB-QUADRATIC STRINGIFICATION (O(n log n))
# =============================================================================
# len(str(list(range(n)))) ≈ n · (3 + log₁₀(n))
#
# How: list(range(n)) → [0, 1, 2, ..., n-1]. Stringified, each number takes
#      its digit count plus ", " separator. Grows slightly faster than linear
#      because larger numbers have more digits.
#
# Formula:  approximately n · log₁₀(n)  (not exact — depends on digit distribution)
#           n=100   → 390
#           n=1000  → 3890
#           n=10000 → 48890
# Parens:   4
# Domain:   n >= 1
#
# Useful for controlled growth into the tens of thousands without the
# wild overshooting of sum(range(n)).

def list_range_repr_len(expr):
    return f'len(str(list(range({expr}))))'


# =============================================================================
# LOGARITHMIC STEP-DOWN
# =============================================================================
# len(str(n)) = floor(log₁₀(n)) + 1
#
# How: Counts the number of decimal digits.
#
# Formula:  f(n) = floor(log₁₀(n)) + 1
# Parens:   2
# Domain:   n >= 0
#
# A "reset switch" — collapses any huge number down to a small one.
# Useful if you overshoot: len(str(1_500_000_000)) = 10.

def log_step_down(expr):
    return f'len(str({expr}))'


# =============================================================================
# BOOLEAN COLLAPSE (reset to 1)
# =============================================================================
# int(bool(n)) = 1   (for any n > 0)
#
# How: Any non-zero int is truthy. bool(n) → True. int(True) → 1.
#
# Formula:  f(n) = 1 for n > 0,  f(0) = 0
# Parens:   2
# Domain:   n >= 0
#
# Instantly collapse any garbage number to 1 without needing a long
# decrement chain. Same cost as the int(not()) base anchor for 1.

def bool_collapse(expr):
    return f'int(bool({expr}))'
