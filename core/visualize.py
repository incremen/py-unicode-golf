"""Step-by-step evaluation of nested builtin expressions.

Evaluates from the inside out: finds the innermost parenthesized call,
evals it, replaces it with the result, and repeats.

Some intermediate results (like property objects or ranges) have repr
strings that aren't valid Python — e.g. repr(property()) gives
"<property object at 0x...>" which can't be eval'd back. These get
stored in a placeholder dict and swapped back to repr for display only.
"""


def find_innermost(expr):
    """Find the innermost parenthesized call. Returns (start, end) or None."""
    last_open = expr.rfind('(')
    if last_open == -1:
        return None
    close = expr.find(')', last_open)
    if close == -1:
        return None
    # Walk back to find the function name
    i = last_open
    while i > 0 and (expr[i - 1].isalpha() or expr[i - 1] == '_'):
        i -= 1
    return i, close + 1


def is_safe_literal(s):
    """Can this repr be pasted back into an expression and eval'd?"""
    try:
        eval(s, {"__builtins__": {}}, {})
        return True
    except Exception:
        return False


def evaluate_steps(expr, max_steps=200):
    """Evaluate an expression from the inside out, returning each step.

    Returns a list of dicts:
      - Normal step: {expr, highlight: {start, end}, call, result}
      - Error step:  {expr, call, error}
      - Final step:  {expr, final: True}
    """
    steps = []
    current = expr
    scope = {}
    placeholder_count = 0

    def make_placeholder(value):
        nonlocal placeholder_count
        name = f'__p{placeholder_count}__'
        placeholder_count += 1
        scope[name] = value
        return name

    def resolve(s):
        for name in sorted(scope, key=len, reverse=True):
            s = s.replace(name, repr(scope[name]))
        return s

    for _ in range(max_steps):
        span = find_innermost(current)
        if not span:
            break

        start, end = span
        call = current[start:end]
        display_expr = resolve(current)
        display_call = resolve(call)
        d_start = len(resolve(current[:start]))

        try:
            result = eval(call, {"__builtins__": __builtins__}, scope)
        except Exception as e:
            steps.append({'expr': display_expr, 'call': display_call, 'error': str(e)})
            break

        result_repr = repr(result)
        steps.append({
            'expr': display_expr,
            'highlight': {'start': d_start, 'end': d_start + len(display_call)},
            'call': display_call,
            'result': result_repr,
        })

        if is_safe_literal(result_repr):
            current = current[:start] + result_repr + current[end:]
        else:
            current = current[:start] + make_placeholder(result) + current[end:]

    steps.append({'expr': resolve(current), 'final': True})
    return steps
