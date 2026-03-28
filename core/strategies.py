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

    'quint_plus_5':   (lambda n: 5 * n + 5,
                       lambda p: f'len(ascii(str(bytes({p}))))'),

    'triangular':     (lambda n: n * (n - 1) // 2,
                       lambda p: f'sum(range({p}))'),

    'enum_list_8x':   (lambda n: 8 * n if 1 <= n <= 10 else -1,
                       lambda p: f'len(str(list(enumerate(bytes({p})))))'),

    'slice_offset':   (lambda n: len(str(n)) + 19 if n > 0 else -1,
                       lambda p: f'len(str(slice({p})))'),

    'complex_offset': (lambda n: len(str(n)) + 5 if n > 0 else -1,
                       lambda p: f'len(str(complex({p})))'),
}

for i in range(1, 6):
    STRATEGIES[f'zip_chain_{i}'] = (
        lambda n, m=3*(i+1): m * n,
        lambda p, k=i: f"len(str(list({'zip(' * k}bytes({p}){')' * k})))"
    )

for i in range(1, 12):
    STRATEGIES[f'ascii_exp_{i}'] = (
        lambda n, m=(1<<i)+3, c=(1<<(i+1))+1: m * n + c,
        lambda p, k=i: f"len({'ascii(' * k}str(bytes({p})){')' * k})"
    )


def apply_strategy(strategy_name, expression):
    if strategy_name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: '{strategy_name}'")
    return STRATEGIES[strategy_name][1](expression)
