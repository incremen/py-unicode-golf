"""Strategies for constructing integers from single-arg Python builtins.

To add a new strategy:
  1. Add a single tuple to the `_build_registry` list.
  2. The forward math and string builders are automatically exported.
"""

def _build_registry():
    """Builds the central registry of all strategies.
    Format: (strategy_name, forward_math_function, string_builder_function)
    """
    registry = [
        ('decrement',      
         lambda n: n - 1,
         lambda expression: f'max(range({expression}))'),
         
        ('triple',         
         lambda n: 3 * n,
         lambda expression: f'len(str(list(bytes({expression}))))'),
         
        ('quad_plus_3',    
         lambda n: 4 * n + 3,
         lambda expression: f'len(str(bytes({expression})))'),
         
        ('quint_plus_5',   
         lambda n: 5 * n + 5,
         lambda expression: f'len(ascii(str(bytes({expression}))))'),
         
        ('triangular',     
         lambda n: n * (n - 1) // 2,
         lambda expression: f'sum(range({expression}))'),
         
        ('enum_list_8x',   
         lambda n: 8 * n if 1 <= n <= 10 else -1,
         lambda expression: f'len(str(list(enumerate(bytes({expression})))))'),
         
        ('slice_offset',   
         lambda n: len(str(n)) + 19 if n > 0 else -1,
         lambda expression: f'len(str(slice({expression})))'),
         
        ('complex_offset', 
         lambda n: len(str(n)) + 5 if n > 0 else -1,
         lambda expression: f'len(str(complex({expression})))'),
    ]

    # ── Parametrized Strategies ──────────────────────────────────────────────

    for zip_count in range(1, 6):
        registry.append((
            f'zip_chain_{zip_count}',
            lambda n, multiplier=3*(zip_count+1): multiplier * n,
            lambda expression, count=zip_count: f"len(str(list({'zip(' * count}bytes({expression}){')' * count})))"
        ))

    for ascii_count in range(1, 12):
        registry.append((
            f'ascii_exp_{ascii_count}',
            lambda n, multiplier=(1<<ascii_count)+3, constant_addition=(1<<(ascii_count+1))+1: multiplier * n + constant_addition,
            lambda expression, count=ascii_count: f"len({'ascii(' * count}str(bytes({expression})){')' * count})"
        ))

    return registry

_STRATEGY_REGISTRY = _build_registry()


FORWARD_STRATEGIES = [
    (strategy_name, math_function)
    for strategy_name, math_function, _ in _STRATEGY_REGISTRY
]

# Quick lookup dictionary used by apply_strategy
_STRING_BUILDERS = {
    strategy_name: string_function 
    for strategy_name, _, string_function in _STRATEGY_REGISTRY
}

def apply_strategy(strategy_name, expression):
    """Retrieves and applies the specific string builder for a given strategy."""
    if strategy_name not in _STRING_BUILDERS:
        raise ValueError(f"Unknown strategy: '{strategy_name}'")
        
    return _STRING_BUILDERS[strategy_name](expression)