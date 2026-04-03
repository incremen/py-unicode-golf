from core.anchors import BASE_ANCHORS

memo = {}


def decrement(expr, times):
    """max(range(n)) = n - 1. Costs 2 parens per step."""
    for _ in range(times):
        expr = f'max(range({expr}))'
    return expr


def triple(expr):
    """len(str(list(bytes(n)))) = 3n exactly. Costs 4 parens."""
    return f'len(str(list(bytes({expr}))))'


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
