"""All known strategies for constructing integers from single-arg Python builtins.

See BASE_ANCHORS in core/anchors.py for the base seeds (0-125).
"""


# n - 1, 2 parens per step, n >= 1
def decrement(expr, times=1):
    for _ in range(times):
        expr = f'max(range({expr}))'
    return expr


# 3n, 4 parens, n >= 1
def multiply_3(expr):
    return f'len(str(list(bytes({expr}))))'


# 4n + 3, 3 parens, n >= 0
def multiply_4_plus_3(expr):
    return f'len(str(bytes({expr})))'


# 5n + 5, 4 parens, n >= 0
def multiply_5_plus_5(expr):
    return f'len(ascii(str(bytes({expr}))))'


# 3(k+1)n, 4+k parens, n >= 1
# k=1: 6n, k=2: 9n, k=3: 12n, ...
def zip_chain(expr, k=1):
    inner = f'bytes({expr})'
    for _ in range(k):
        inner = f'zip({inner})'
    return f'len(str(list({inner})))'


# (2^k + 3)n + (2^(k+1) + 1), 3+k parens, n >= 0
# k=1: 5n+5, k=2: 7n+9, k=3: 11n+17, k=4: 19n+33, k=5: 35n+65, k=6: 67n+129
def ascii_exp(expr, k=1):
    inner = f'str(bytes({expr}))'
    for _ in range(k):
        inner = f'ascii({inner})'
    return f'len({inner})'


# n(n-1)/2, 2 parens, n >= 0
def triangular_sum(expr):
    return f'sum(range({expr}))'


# 3n (but 4 at n=1), 4 parens, n >= 1
def multiply_3_tuple(expr):
    return f'len(str(tuple(bytes({expr}))))'


# 6n for n < 10, 5 parens, n >= 1
def enumerate_dict(expr):
    return f'len(str(dict(enumerate(bytearray({expr})))))'


# ~n*log10(n), 4 parens, n >= 1
def range_str_length(expr):
    return f'len(str(list(range({expr}))))'


# floor(log10(n)) + 1, 2 parens, n >= 0
def digit_count(expr):
    return f'len(str({expr}))'


# ── Quick reference ──────────────────────────────────────────────────
#
#  Formula       Parens  Expression
#  n - 1           2     max(range(n))
#  3n              4     len(str(list(bytes(n))))
#  4n + 3          3     len(str(bytes(n)))
#  5n + 5          4     len(ascii(str(bytes(n))))
#  3(k+1)n       4+k     len(str(list(zip^k(bytes(n)))))
#  (2^k+3)n+..   3+k     len(ascii^k(str(bytes(n))))
#  n(n-1)/2        2     sum(range(n))
#  1               2     int(bool(n))
