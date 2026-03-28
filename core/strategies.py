"""String-generation strategies for builtin-only integer expressions."""


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
