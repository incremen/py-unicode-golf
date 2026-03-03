import sys

# str(not()) == "True", min("True") == "T", ord("T") == 84
BASE_EXPR = 'ord(min(str(not())))'
BASE_VAL = 84

# next(reversed(range(n))) == n - 1
DECREMENT = 'next(reversed(range({})))'

# sum(range(k)) == k * (k-1) / 2  (triangular number)
TRIANGULAR = 'sum(range({}))'


def decrement(expr, times):
    """Wrap expr in n layers of next(reversed(range(...))) to subtract n."""
    for _ in range(times):
        expr = DECREMENT.format(expr)
    return expr


def build_n(n):
    """Build an expression that evaluates to n, using no numeric literals."""
    if n <= BASE_VAL:
        return decrement(BASE_EXPR, BASE_VAL - n)

    # For n > 84, find the smallest triangular number >= n,
    # then decrement down to n.
    for k in range(2, BASE_VAL + 1):
        triangular = k * (k - 1) // 2
        if triangular >= n:
            expr = TRIANGULAR.format(build_n(k))
            return decrement(expr, triangular - n)

    raise ValueError(f"Cannot construct {n} (max supported: 3486)")


def char_to_expr(char):
    """Convert a character to a pure-builtin Python expression."""
    return f'chr({build_n(ord(char))})'


if __name__ == '__main__':
    char = input("Enter a character: ")
    if len(char) != 1:
        print("Please enter exactly one character.")
        sys.exit(1)

    expr = char_to_expr(char)
    print(f"\nExpression for '{char}' (code point {ord(char)}):")
    print(expr)
    print(f"\nVerify: eval gives '{eval(expr)}'")
