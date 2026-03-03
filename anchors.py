"""Build Python expressions for any integer using only builtin calls — no numeric literals.

Approach:
  1. Base anchors: numbers directly constructible (e.g., ord(min(str(not()))) = 84)
  2. Expand via sum(range(k)) = k*(k-1)/2  (triangular numbers)
  3. Reach any target by decrementing from the nearest anchor above it,
     using max(range(n)) = n - 1
"""

# ── Base anchors ─────────────────────────────────────────────────────────
# Numbers we can construct with short, direct expressions.
# The comments show the intermediate string value that produces each number.

# fmt: off
BASE_ANCHORS = {
    #      expression                                 intermediate → value
    0:   'int(not(not()))',                          # False       → 0
    1:   'int(not())',                               # True        → 1
    2:   'len(str(ord(min(str(not())))))',            # "84"        → 2
    3:   'len(bin(int(not())))',                      # "0b1"       → 3
    4:   'len(str(not()))',                           # "True"      → 4
    5:   'len(bin(len(str(not()))))',                 # "0b100"     → 5
    6:   'sum(range(len(str(not()))))',               # range(4)    → 6
    11:  'len(str(frozenset()))',                     # "frozenset()" → 11
    13:  'len(str(type(int())))',                     # "<class 'int'>"   → 13
    14:  'len(str(type(not())))',                     # "<class 'bool'>"  → 14
    15:  'len(str(type(float())))',                   # "<class 'float'>" → 15
    32:  'ord(min(str(type(not()))))',                # ' ' in "<class 'bool'>"
    39:  'ord(min(str(bytes())))',                    # "'" in "b''"
    40:  'ord(min(str(tuple())))',                    # '(' in "()"
    41:  'ord(max(str(tuple())))',                    # ')' in "()"
    46:  'ord(min(str(float())))',                    # '.' in "0.0"
    48:  'ord(max(str(float())))',                    # '0' in "0.0"
    70:  'ord(min(str(not(not()))))',                 # 'F' in "False"
    84:  'ord(min(str(not())))',                      # 'T' in "True"
    91:  'ord(min(str(list())))',                     # '[' in "[]"
    93:  'ord(max(str(list())))',                     # ']' in "[]"
    98:  'ord(max(str(bytes())))',                    # 'b' in "b''"
    106: 'ord(max(str(complex())))',                  # 'j' in "0j"
    111: 'ord(max(oct(int(not()))))',                 # 'o' in "0o1"
    115: 'ord(max(str(not(not()))))',                 # 's' in "False"
    116: 'ord(max(str(set())))',                      # 't' in "set()"
    117: 'ord(max(str(not())))',                      # 'u' in "True"
    120: 'ord(max(hex(int(not()))))',                 # 'x' in "0x1"
    121: 'ord(max(str(type(type(not())))))',          # 'y' in "<class 'type'>"
    122: 'ord(max(str(frozenset())))',                # 'z' in "frozenset()"
    123: 'ord(min(str(dict())))',                     # '{' in "{}"
    125: 'ord(max(str(dict())))',                     # '}' in "{}"
}
# fmt: on


# ── Operations ───────────────────────────────────────────────────────────

def decrement(expr, times):
    """Apply max(range(expr)) `times` times — each subtracts 1."""
    for _ in range(times):
        expr = f'max(range({expr}))'
    return expr


def triangular(expr):
    """Apply sum(range(expr)) — gives the triangular number T(n) = n*(n-1)/2."""
    return f'sum(range({expr}))'


# ── Anchor expansion ─────────────────────────────────────────────────────

def expand_anchors(base, max_val=100_000):
    """Grow anchor set by applying sum(range()) to each existing anchor."""
    anchors = dict(base)
    changed = True
    while changed:
        changed = False
        for n, expr in sorted(list(anchors.items())):
            if n < 2:
                continue
            tri = n * (n - 1) // 2
            if 0 < tri <= max_val and tri not in anchors:
                anchors[tri] = triangular(expr)
                changed = True
    return anchors


ANCHORS = expand_anchors(BASE_ANCHORS)


# ── Building expressions ─────────────────────────────────────────────────

sorted_anchors = sorted(ANCHORS.items())
memo = dict(ANCHORS)


def nearest_anchor_above(n):
    """Find the smallest anchor value >= n. Returns (gap, expr) or None."""
    for val, expr in sorted_anchors:
        if val >= n:
            return val - n, expr
    return None


def nearest_triangular_above(n):
    """Find the smallest k where T(k) >= n. Returns (k, gap) or None."""
    for k in range(2, 200_000):
        tri = k * (k - 1) // 2
        if tri >= n:
            return k, tri - n
    return None


def build_n(n):
    """Build an expression that evaluates to integer n, using no numeric literals."""
    if n in memo:
        return memo[n]

    direct = nearest_anchor_above(n)
    tri = nearest_triangular_above(n)

    direct_gap = direct[0] if direct else float('inf')
    tri_gap = tri[1] if tri else float('inf')

    # Pick whichever needs fewer decrements at this level
    if direct_gap <= tri_gap:
        result = decrement(direct[1], direct_gap)
    else:
        k, gap = tri
        result = decrement(triangular(build_n(k)), gap)

    memo[n] = result
    return result


def build_char(char):
    """Build a chr(...) expression for a single character."""
    return f'chr({build_n(ord(char))})'


# ── Self-test ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("Base anchors:")
    for val in sorted(BASE_ANCHORS):
        expr = BASE_ANCHORS[val]
        ok = "✓" if eval(expr) == val else "✗"
        print(f"  {ok} {val:>5} = {expr}")

    print(f"\nExpanded to {len(ANCHORS)} anchors via sum(range())")
    print(f"Sorted: {sorted(ANCHORS)[:20]}...")
