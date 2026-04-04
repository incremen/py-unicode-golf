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
    ('str(type(iter(range(int()))))',           str(type(iter(range(int()))))),    # "<class 'range_iterator'>"
    ('str(type(reversed(list())))',             str(type(reversed(list())))),      # "<class 'list_reverseiterator'>"
    ('str(type(reversed(dict())))',             str(type(reversed(dict())))),      # "<class 'dict_reversekeyiterator'>"
    ('str(type(reversed(tuple())))',            str(type(reversed(tuple())))),     # "<class 'reversed'>"

    # exception type reprs (shorter len expressions for 20, 23)
    ('str(type(ValueError()))',                 str(type(ValueError()))),          # "<class 'ValueError'>"
    ('str(type(StopIteration()))',              str(type(StopIteration()))),       # "<class 'StopIteration'>"
]


def _add_if_better(n, expr):
    existing = BASE_ANCHORS.get(n)
    if existing is None or existing.count('(') > expr.count('('):
        BASE_ANCHORS[n] = expr

for expr, val in _STRING_EXPRS:
    _add_if_better(len(val),                              f'len({expr})')
    if val:
        _add_if_better(ord(min(val)),                     f'ord(min({expr}))')
        _add_if_better(ord(max(val)),                     f'ord(max({expr}))')
        _add_if_better(ord(next(iter(val))),              f'ord(next(iter({expr})))')
        _add_if_better(ord(next(reversed(val))),          f'ord(next(reversed({expr})))')
        _add_if_better(ord(next(reversed(hex(len(val))))),f'ord(next(reversed(hex(len({expr})))))')
        _add_if_better(ord(next(reversed(oct(len(val))))),f'ord(next(reversed(oct(len({expr})))))')


