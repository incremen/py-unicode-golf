"""Build Python expressions for any integer using only builtin calls — no numeric literals.

Approach:
  1. Base anchors: numbers directly constructible (e.g., ord(min(str(not()))) = 84)
  2. Expand via sum(range(k)) = k*(k-1)/2  (triangular numbers)
  3. Reach any target by finding a nearby anchor/triangular and decrementing
     with next(reversed(range(n))) = n - 1
"""

# fmt: off
BASE_ANCHORS = {
    # not()/not(not()) → True/False, then type conversions
    0:   'int(not(not()))',                        # int(False)
    1:   'int(not())',                             # int(True)

    # len() on string representations
    2:   'len(str(ord(min(str(not())))))',          # len("84")
    3:   'len(bin(int(not())))',                    # len("0b1")
    4:   'len(str(not()))',                         # len("True")
    5:   'len(bin(len(str(not()))))',               # len("0b100")
    6:   'sum(range(len(str(not()))))',             # sum(range(4))
    11:  'len(str(frozenset()))',                   # len("frozenset()")
    13:  'len(str(type(int())))',                   # len("<class 'int'>")
    14:  'len(str(type(not())))',                   # len("<class 'bool'>")
    15:  'len(str(type(float())))',                 # len("<class 'float'>")

    # ord() on characters from string representations
    32:  'ord(min(str(type(not()))))',              # ' ' from "<class 'bool'>"
    39:  'ord(min(str(bytes())))',                  # "'" from "b''"
    40:  'ord(min(str(tuple())))',                  # '(' from "()"
    41:  'ord(max(str(tuple())))',                  # ')' from "()"
    46:  'ord(min(str(float())))',                  # '.' from "0.0"
    48:  'ord(max(str(float())))',                  # '0' from "0.0"
    70:  'ord(min(str(not(not()))))',               # 'F' from "False"
    84:  'ord(min(str(not())))',                    # 'T' from "True"
    91:  'ord(min(str(list())))',                   # '[' from "[]"
    93:  'ord(max(str(list())))',                   # ']' from "[]"
    98:  'ord(max(str(bytes())))',                  # 'b' from "b''"
    106: 'ord(max(str(complex())))',               # 'j' from "0j"
    111: 'ord(max(oct(int(not()))))',              # 'o' from "0o1"
    115: 'ord(max(str(not(not()))))',              # 's' from "False"
    116: 'ord(max(str(set())))',                   # 't' from "set()"
    117: 'ord(max(str(not())))',                   # 'u' from "True"
    120: 'ord(max(hex(int(not()))))',              # 'x' from "0x1"
    121: 'ord(max(str(type(type(not())))))',       # 'y' from "<class 'type'>"
    122: 'ord(max(str(frozenset())))',             # 'z' from "frozenset()"
    123: 'ord(min(str(dict())))',                  # '{' from "{}"
    125: 'ord(max(str(dict())))',                  # '}' from "{}"
}
# fmt: on


def _decrement(expr, times):
    """Wrap expr in next(reversed(range(...))) `times` times to subtract."""
    for _ in range(times):
        expr = f'next(reversed(range({expr})))'
    return expr


def _expand_anchors(base, max_val=100_000):
    """Grow anchor set by applying sum(range(n)) = n*(n-1)/2 to each anchor."""
    anchors = dict(base)
    changed = True
    while changed:
        changed = False
        for n, expr in sorted(list(anchors.items())):
            if n < 2:
                continue
            tri = n * (n - 1) // 2
            if 0 < tri <= max_val and tri not in anchors:
                anchors[tri] = f'sum(range({expr}))'
                changed = True
    return anchors


ANCHORS = _expand_anchors(BASE_ANCHORS)

_memo = dict(ANCHORS)


def build_n(n):
    """Build an expression that evaluates to integer n, using no numeric literals."""
    if n in _memo:
        return _memo[n]

    # Option A: decrement from nearest anchor above n
    direct_gap = None
    for val in sorted(ANCHORS):
        if val >= n:
            direct_gap = val - n
            direct_expr = ANCHORS[val]
            break

    # Option B: find smallest k where T(k) = k*(k-1)/2 >= n, then decrement
    tri_gap = None
    tri_k = None
    for k in range(2, 200_000):
        tri = k * (k - 1) // 2
        if tri >= n:
            tri_gap = tri - n
            tri_k = k
            break

    # Pick whichever needs fewer decrements at this level
    if direct_gap is not None and (tri_gap is None or direct_gap <= tri_gap):
        result = _decrement(direct_expr, direct_gap)
    else:
        k_expr = build_n(tri_k)
        result = _decrement(f'sum(range({k_expr}))', tri_gap)

    _memo[n] = result
    return result


def build_char(char):
    """Build a chr(...) expression for a single character."""
    return f'chr({build_n(ord(char))})'


if __name__ == '__main__':
    # Show base anchors and verify them
    print("Base anchors:")
    for val in sorted(BASE_ANCHORS):
        expr = BASE_ANCHORS[val]
        actual = eval(expr)
        ok = "✓" if actual == val else "✗"
        print(f"  {ok} {val:>5} = {expr}")

    print(f"\nExpanded to {len(ANCHORS)} anchors via sum(range())")
    print(f"Sorted: {sorted(ANCHORS)[:20]}...")
