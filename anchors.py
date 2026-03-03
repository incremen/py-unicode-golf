"""Build Python expressions for any integer using only builtin calls — no numeric literals.

Approach:
  1. Base anchors: numbers directly constructible (e.g., ord(min(str(not()))) = 84)
  2. Expand via operations like sum(range()), len(str(list(range()))), etc.
  3. Reach any target by decrementing from the nearest anchor above it,
     using max(range(n)) = n - 1
"""

# ── Base anchors ─────────────────────────────────────────────────────────
# Numbers we can construct directly from zero-arg builtins.
# Grouped by technique, comments show the derivation.

# fmt: off
BASE_ANCHORS = {
    # ── Booleans → ints ──
    0:   'int(not(not()))',                          # int(False)
    1:   'int(not())',                               # int(True)

    # ── len() on string reprs ──
    2:   'len(str(ord(min(str(not())))))',            # len("84")
    3:   'len(bin(int(not())))',                      # len("0b1")
    4:   'len(str(not()))',                           # len("True")
    5:   'len(bin(len(str(not()))))',                 # len("0b100")
    6:   'sum(range(len(str(not()))))',               # sum(range(4))
    11:  'len(str(frozenset()))',                     # len("frozenset()")

    # ── len() on type name strings ──
    13:  'len(str(type(int())))',                     # "<class 'int'>"
    14:  'len(str(type(not())))',                     # "<class 'bool'>"
    15:  'len(str(type(float())))',                   # "<class 'float'>"
    17:  'len(str(type(complex())))',                 # "<class 'complex'>"
    18:  'len(str(type(reversed(str()))))',           # "<class 'reversed'>"
    19:  'len(str(type(frozenset())))',               # "<class 'frozenset'>"

    # ── len() on iterator/reversed type name strings ──
    22:  'len(str(type(iter(set()))))',               # "<class 'set_iterator'>"
    23:  'len(str(type(iter(list()))))',              # "<class 'list_iterator'>"
    24:  'len(str(type(iter(bytes()))))',             # "<class 'bytes_iterator'>"
    26:  'len(str(type(iter(dict()))))',              # "<class 'dict_keyiterator'>"
    28:  'len(str(type(iter(str()))))',               # "<class 'str_ascii_iterator'>"
    30:  'len(str(type(reversed(list()))))',          # "<class 'list_reverseiterator'>"
    33:  'len(str(type(reversed(dict()))))',          # "<class 'dict_reversekeyiterator'>"

    # ── ord(min/max(repr)) — pick chars from string reprs ──
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
# Each takes an expression string and returns a new expression string.

def decrement(expr, times):
    """max(range(n)) = n - 1. Costs 2 parens per step."""
    for _ in range(times):
        expr = f'max(range({expr}))'
    return expr


def triangular(expr):
    """sum(range(n)) = n*(n-1)/2. Costs 2 parens."""
    return f'sum(range({expr}))'


def list_repr_len(expr):
    """len(str(list(range(n)))) ≈ 4n. Costs 4 parens."""
    return f'len(str(list(range({expr}))))'


def bytes_repr_len(expr):
    """len(str(bytes(range(n)))) ≈ 2n. Costs 4 parens. Only valid for n ≤ 256."""
    return f'len(str(bytes(range({expr}))))'


def bytearray_repr_len(expr):
    """len(str(bytearray(range(n)))) ≈ 2n. Costs 4 parens. Only valid for n ≤ 256."""
    return f'len(str(bytearray(range({expr}))))'


# ── Anchor expansion ─────────────────────────────────────────────────────

def expand_anchors(base, max_val=200_000):
    """Grow the anchor set by repeatedly applying growing operations.

    Each iteration applies every operation to every anchor and keeps
    results that are new or cheaper (fewer parens) than existing entries.
    Loops until no new anchors are found.
    """
    anchors = dict(base)
    changed = True
    while changed:
        changed = False
        for n, expr in sorted(list(anchors.items())):
            if n < 2:
                continue

            candidates = []

            # Triangular: n → n*(n-1)/2
            tri = n * (n - 1) // 2
            if 0 < tri <= max_val:
                candidates.append((tri, triangular(expr)))

            # List repr: n → ~4n
            try:
                val = len(str(list(range(n))))
                if 0 < val <= max_val:
                    candidates.append((val, list_repr_len(expr)))
            except (OverflowError, MemoryError):
                pass

            # Bytes repr: n → ~2n (n ≤ 256 only)
            if n <= 256:
                val = len(str(bytes(range(n))))
                if 0 < val <= max_val:
                    candidates.append((val, bytes_repr_len(expr)))

            # Bytearray repr: n → ~2n (n ≤ 256 only)
            if n <= 256:
                val = len(str(bytearray(range(n))))
                if 0 < val <= max_val:
                    candidates.append((val, bytearray_repr_len(expr)))

            for val, new_expr in candidates:
                if val not in anchors or new_expr.count('(') < anchors[val].count('('):
                    anchors[val] = new_expr
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

    print(f"\nExpanded to {len(ANCHORS)} anchors")
    print(f"Range: {min(ANCHORS)} to {max(ANCHORS)}")
