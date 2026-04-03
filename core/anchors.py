# ── Base anchors ─────────────────────────────────────────────────────────
# Numbers we can construct directly from zero-arg builtins.

# Anchors that don't fall out of the len/ord pattern below.
BASE_ANCHORS = {
    0: 'int(not(not()))',
    1: 'int(not())',
    6: 'sum(range(len(str(not()))))',  # sum(range(4))
}

# ── String expressions ────────────────────────────────────────────────────
# Each entry: (expression_string, value_of_that_expression).
# For each one we try len(...), ord(min(...)), ord(max(...)) and keep the
# best (fewest parens) expression for each resulting integer.

_STRING_EXPRS = [
    # direct value reprs
    ('str(not())',                              str(not())),            # 'True'
    ('str(not(not()))',                         str(not(not()))),       # 'False'
    ('str(list())',                             str(list())),           # '[]'
    ('str(tuple())',                            str(tuple())),          # '()'
    ('str(dict())',                             str(dict())),           # '{}'
    ('str(set())',                              str(set())),            # 'set()'
    ('str(bytes())',                            str(bytes())),          # "b''"
    ('str(float())',                            str(float())),          # '0.0'
    ('str(complex())',                          str(complex())),        # '0j'
    ('str(frozenset())',                        str(frozenset())),      # 'frozenset()'

    # numeric string reprs (bin/hex/oct already return strings)
    ('bin(int(not()))',                         bin(int(not()))),       # '0b1'
    ('hex(int(not()))',                         hex(int(not()))),       # '0x1'
    ('oct(int(not()))',                         oct(int(not()))),       # '0o1'

    # type name reprs
    ('str(type(int()))',                        str(type(int()))),      # "<class 'int'>"
    ('str(type(not()))',                        str(type(not()))),      # "<class 'bool'>"
    ('str(type(float()))',                      str(type(float()))),    # "<class 'float'>"
    ('str(type(complex()))',                    str(type(complex()))),  # "<class 'complex'>"
    ('str(type(property()))',                   str(type(property()))), # "<class 'property'>"
    ('str(type(frozenset()))',                  str(type(frozenset()))),# "<class 'frozenset'>"
    ('str(type(memoryview(bytes())))',          str(type(memoryview(bytes())))),   # "<class 'memoryview'>"
    ('str(type(classmethod(int())))',           str(type(classmethod(int())))),    # "<class 'classmethod'>"
    ('str(type(type(not())))',                  str(type(type(not())))),           # "<class 'type'>"

    # iterator/reversed type reprs
    ('str(type(iter(set())))',                  str(type(iter(set())))),           # "<class 'set_iterator'>"
    ('str(type(iter(list())))',                 str(type(iter(list())))),          # "<class 'list_iterator'>"
    ('str(type(iter(bytes())))',                str(type(iter(bytes())))),         # "<class 'bytes_iterator'>"
    ('str(type(iter(dict())))',                 str(type(iter(dict())))),          # "<class 'dict_keyiterator'>"
    ('str(type(iter(str())))',                  str(type(iter(str())))),           # "<class 'str_ascii_iterator'>"
    ('str(type(reversed(list())))',             str(type(reversed(list())))),      # "<class 'list_reverseiterator'>"
    ('str(type(reversed(dict())))',             str(type(reversed(dict())))),      # "<class 'dict_reversekeyiterator'>"
]


def _add_if_better(n, expr):
    existing = BASE_ANCHORS.get(n)
    if existing is None or existing.count('(') > expr.count('('):
        BASE_ANCHORS[n] = expr

for expr, val in _STRING_EXPRS:
    _add_if_better(len(val),                    f'len({expr})')
    if val:
        _add_if_better(ord(min(val)),           f'ord(min({expr}))')
        _add_if_better(ord(max(val)),           f'ord(max({expr}))')
        _add_if_better(ord(next(iter(val))),    f'ord(next(iter({expr})))')
        _add_if_better(ord(next(reversed(val))),f'ord(next(reversed({expr})))')


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

    if n in BASE_ANCHORS:
        memo[n] = BASE_ANCHORS[n]
        return memo[n]

    q = -(-n // 3)
    r = 3 * q - n

    result = decrement(triple(build_n(q)), r)
    memo[n] = result
    return result


def build_char(char):
    """Build a chr(...) expression for a single character."""
    return f'chr({build_n(ord(char))})'


def build_string(text):
    """Build a string expression using reversed(range()) iterators + eval.

    Pattern: eval(bytes(next(zip(reversed(range(b1+1)), reversed(range(b2+1)), ...))))
    where each bi is a UTF-8 byte of repr(text).
    reversed(range(b+1)) yields b as its first element.
    zip packs them, next pulls the tuple, bytes makes the repr string, eval parses it.
    No uncalled function references — every argument is a function call result.
    """
    if len(text) == 1:
        return build_char(text)

    repr_bytes = repr(text).encode('utf-8')
    rev_exprs = [f'reversed(range({build_n(b + 1)}))' for b in repr_bytes]
    return f'eval(bytes(next(zip({",".join(rev_exprs)}))))'
