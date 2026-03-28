"""String-generation strategies for builtin-only integer expressions.

To add a new strategy:
  1. Add its string-builder to STRATEGIES (or apply_parametrized_strategy for k-variants)
  2. Add its forward math function to FORWARD_STRATEGIES
  Both are imported by the Dijkstra optimizer automatically.
"""


# ── String builders ──────────────────────────────────────────────────────────
# Used by apply_strategy() to produce the actual expression string.

STRATEGIES = {
    'base':           lambda p: p,
    'decrement':      lambda p: f'max(range({p}))',
    'triple':         lambda p: f'len(str(list(bytes({p}))))',
    'quad_plus_3':    lambda p: f'len(str(bytes({p})))',
    'quint_plus_5':   lambda p: f'len(ascii(str(bytes({p}))))',
    'triangular':     lambda p: f'sum(range({p}))',
    'enum_list_8x':   lambda p: f'len(str(list(enumerate(bytes({p})))))',
    'slice_offset':   lambda p: f'len(str(slice({p})))',
    'complex_offset': lambda p: f'len(str(complex({p})))',
}


def apply_parametrized_strategy(strategy, parent_expr):
    """Handle strategies with a numeric suffix: ascii_exp_k and zip_chain_k."""
    if strategy.startswith('ascii_exp_'):
        k = int(strategy.split('_')[-1])
        inner = f'str(bytes({parent_expr}))'
        for _ in range(k):
            inner = f'ascii({inner})'
        return f'len({inner})'
    if strategy.startswith('zip_chain_'):
        k = int(strategy.split('_')[-1])
        inner = f'bytes({parent_expr})'
        for _ in range(k):
            inner = f'zip({inner})'
        return f'len(str(list({inner})))'
    return None


# ── Forward math functions ───────────────────────────────────────────────────
# Used by the Dijkstra optimizer to traverse the integer graph.
# Each entry: (name, forward_fn) where forward_fn(n) -> target integer.

def _build_forward_strategies():
    strategies_list = [
        ('decrement',      lambda n: n - 1),
        ('triple',         lambda n: 3 * n),
        ('quad_plus_3',    lambda n: 4 * n + 3),
        ('quint_plus_5',   lambda n: 5 * n + 5),
        ('triangular',     lambda n: n * (n - 1) // 2),
        ('enum_list_8x',   lambda n: 8 * n if 1 <= n <= 10 else -1),
        ('slice_offset',   lambda n: len(str(n)) + 19 if n > 0 else -1),
        ('complex_offset', lambda n: len(str(n)) + 5  if n > 0 else -1),
    ]
    for zip_count in range(1, 6):
        strategies_list.append((
            f'zip_chain_{zip_count}',
            lambda n, m=3*(zip_count+1): m * n
        ))
    for ascii_count in range(1, 12):
        strategies_list.append((
            f'ascii_exp_{ascii_count}',
            lambda n, m=(1<<ascii_count)+3, c=(1<<(ascii_count+1))+1: m * n + c
        ))
    return strategies_list

FORWARD_STRATEGIES = _build_forward_strategies()


def apply_strategy(strategy, parent_expr, offset=0):
    """Apply a named strategy to parent_expr, then apply `offset` additional decrements."""
    if strategy in STRATEGIES:
        expr = STRATEGIES[strategy](parent_expr)
    else:
        expr = apply_parametrized_strategy(strategy, parent_expr)
        if expr is None:
            raise ValueError(f'Unknown strategy: {strategy}')

    for _ in range(offset):
        expr = f'max(range({expr}))'

    return expr
