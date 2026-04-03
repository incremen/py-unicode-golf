"""Strategies for constructing integers from single-arg Python builtins.

Each entry: name -> (forward_math_fn, string_builder_fn)
  forward_math_fn(n)      -> target integer  (used by Dijkstra)
  string_builder_fn(expr) -> expression str  (used by apply_strategy)

To add a new strategy, add one entry to STRATEGIES.
"""

STRATEGIES = {
    'decrement':      (lambda n: n - 1,
                       lambda p: f'max(range({p}))'),

    'triple':         (lambda n: 3 * n,
                       lambda p: f'len(str(list(bytes({p}))))'),

    'quad_plus_3':    (lambda n: 4 * n + 3,
                       lambda p: f'len(str(bytes({p})))'),


    'triangular':     (lambda n: n * (n - 1) // 2,
                       lambda p: f'sum(range({p}))'),

    'enum_list_8x':   (lambda n: 8 * n if 1 <= n <= 10 else -1,
                       lambda p: f'len(str(list(enumerate(bytes({p})))))'),

    'slice_offset':   (lambda n: len(str(n)) + 19 if n > 0 else -1,
                       lambda p: f'len(str(slice({p})))'),

    'complex_offset': (lambda n: len(str(n)) + 5 if n > 0 else -1,
                       lambda p: f'len(str(complex({p})))'),
}

for i in range(1, 20):
    STRATEGIES[f'zip_chain_{i}'] = (
        lambda n, m=3*(i+1): m * n,
        lambda p, k=i: f"len(str(list({'zip(' * k}bytes({p}){')' * k})))"
    )

for i in range(1, 20):
    STRATEGIES[f'ascii_exp_{i}'] = (
        lambda n, m=(1<<i)+3, c=(1<<(i+1))+1: m * n + c,
        lambda p, k=i: f"len({'ascii(' * k}str(bytes({p})){')' * k})"
    )


# ── Lookup tables for non-linear strategies ───────────────────────────────────
# Precomputed once at import time using O(1)-per-step incremental formulas.

_MAX = 200_000
_DIGIT_SUM       = [0] * (_MAX + 1)
_LIST_RANGE_LEN  = [0] * (_MAX + 1)
_TUPLE_RANGE_LEN = [0] * (_MAX + 1)
_ZIP_RANGE_LEN   = [0] * (_MAX + 1)
_DICT_ENUM_RANGE = [0] * (_MAX + 1)

_LIST_RANGE_LEN[0] = _TUPLE_RANGE_LEN[0] = _ZIP_RANGE_LEN[0] = _DICT_ENUM_RANGE[0] = 2
_TUPLE_RANGE_LEN[1] = 4  # "(0,)" has trailing comma

for _n in range(1, _MAX + 1):
    _DIGIT_SUM[_n]        = _DIGIT_SUM[_n - 1] + len(str(_n - 1))
    _LIST_RANGE_LEN[_n]   = 2 + _DIGIT_SUM[_n] + 2 * (_n - 1)
    if _n >= 2:
        _TUPLE_RANGE_LEN[_n] = 2 + _DIGIT_SUM[_n] + 2 * (_n - 1)
    _ZIP_RANGE_LEN[_n]    = _DIGIT_SUM[_n] + 5 * _n
    _DICT_ENUM_RANGE[_n]  = 2 * _DIGIT_SUM[_n] + 4 * _n


STRATEGIES.update({
    'bytearray_4x':   (lambda n: 4 * n + 14,
                       lambda p: f'len(str(bytearray({p})))'),

    'bin_len':        (lambda n: n.bit_length() + 2 if n > 0 else 3,
                       lambda p: f'len(bin({p}))'),

    'hex_len':        (lambda n: len(hex(n)),
                       lambda p: f'len(hex({p}))'),

    'oct_len':        (lambda n: len(oct(n)),
                       lambda p: f'len(oct({p}))'),

    'ascii_range':    (lambda n: len(str(n)) + 10,
                       lambda p: f'len(ascii(range({p})))'),

    'list_range':     (lambda n: _LIST_RANGE_LEN[n]  if n <= _MAX else -1,
                       lambda p: f'len(str(list(range({p}))))'),

    'tuple_range':    (lambda n: _TUPLE_RANGE_LEN[n] if n <= _MAX else -1,
                       lambda p: f'len(str(tuple(range({p}))))'),

    'zip_range':      (lambda n: _ZIP_RANGE_LEN[n]   if n <= _MAX else -1,
                       lambda p: f'len(str(list(zip(range({p})))))'),

    'dict_enum_range':(lambda n: _DICT_ENUM_RANGE[n] if 0 <= n <= _MAX else -1,
                       lambda p: f'len(str(dict(enumerate(range({p})))))'),

    'list_enum_bytes':(lambda n: _DIGIT_SUM[n] + 6 * n + 2 if n > 0 else 2,
                       lambda p: f'len(str(list(enumerate(bytes({p})))))'),

    'dict_enum_bytes':(lambda n: _DIGIT_SUM[n] + 5 * n + 2 if n > 0 else 2,
                       lambda p: f'len(str(dict(enumerate(bytes({p})))))'),

    'digit_ord':      (lambda n: ord(str(n)) if 0 <= n <= 9 else -1,
                       lambda p: f'ord(str({p}))'),
})


def apply_strategy(strategy_name, expression):
    if strategy_name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: '{strategy_name}'")
    return STRATEGIES[strategy_name][1](expression)
