"""Build Python expressions for any integer using only builtin calls — no numeric literals.

Core insight: len(str(list(bytes(n)))) = 3n exactly.
Combined with max(range(n)) = n - 1, any number can be built in base 3
by interleaving 3x multiplications with 0-2 decrements per level.

Budget for all of Unicode (max 1,114,111):
  - 13 levels of 3x (4 parens each) = 52
  - up to 2 decrements per level (2 parens each) = 52
  - seed anchor ~4 + chr() 1 = 5
  - total: ~109 parens, well under 200
"""

# ── Base anchors ─────────────────────────────────────────────────────────
# Numbers we can construct directly from zero-arg builtins.

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
    18:  'len(str(type(property())))',                # "<class 'property'>"
    19:  'len(str(type(frozenset())))',               # "<class 'frozenset'>"
    20:  'len(str(type(memoryview(bytes()))))',       # "<class 'memoryview'>"
    21:  'len(str(type(classmethod(int()))))',        # "<class 'classmethod'>"

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

def decrement(expr, times):
    """max(range(n)) = n - 1. Costs 2 parens per step."""
    for _ in range(times):
        expr = f'max(range({expr}))'
    return expr


def triple(expr):
    """len(str(list(bytes(n)))) = 3n exactly. Costs 4 parens."""
    return f'len(str(list(bytes({expr}))))'


# ── Building expressions ─────────────────────────────────────────────────

memo = {}


def build_n(n):
    """Build an expression evaluating to n, using no numeric literals.

    Strategy: build n in base 3 by interleaving 3x multiplications
    with 0-2 decrements per level. Works for any non-negative integer.
    """
    if n in memo:
        return memo[n]

    # Use base anchor if it's an exact hit
    if n in BASE_ANCHORS:
        memo[n] = BASE_ANCHORS[n]
        return memo[n]

    # Base-3 decomposition: n = 3 * (n // 3) + (n % 3)
    # Build n//3 recursively, then apply 3x, then decrement by (n%3) if needed.
    # But we actually need to go the other way: find q,r such that n = 3q + r.
    # We build q, triple it to get 3q, then... we need to ADD r, but we can
    # only subtract. So instead: n = 3q - r where r ∈ {0, 1, 2}.
    # This means q = ceil(n/3), r = 3q - n.
    q = -(-n // 3)  # ceiling division
    r = 3 * q - n   # r ∈ {0, 1, 2}

    result = decrement(triple(build_n(q)), r)
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

    # Test coverage
    print("\nTesting all printable ASCII...")
    for i in range(32, 127):
        expr = build_char(chr(i))
        assert eval(expr) == chr(i), f"FAIL at {i}"
    print("  All passed.")

    print("\nSample expressions:")
    for c in ['a', 'Z', '0', '~']:
        expr = build_char(c)
        depth = expr.count('(')
        print(f"  {c!r} ({ord(c):>3}): depth={depth:>3}  {expr}")

    # Test a big Unicode char
    expr = build_char(chr(3486))  # ඞ
    depth = expr.count('(')
    print(f"  ඞ (3486): depth={depth:>3}  verified={eval(expr) == chr(3486)}")

    expr = build_char(chr(128512))  # 😀
    depth = expr.count('(')
    print(f"  😀 (128512): depth={depth:>3}  verified={eval(expr) == chr(128512)}")
