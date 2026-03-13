"""Step-by-step evaluation of nested builtin expressions.

Evaluates from the inside out: finds the innermost parenthesized call,
evals it, replaces it with the result, and repeats.

Some intermediate results (like property objects or ranges) have repr
strings that aren't valid Python - e.g. repr(property()) gives
"<property object at 0x...>" which can't be eval'd back. These get
stored in a placeholder dict and swapped back to repr for display only.
"""


def find_innermost(expr):
    """Find the innermost function call. Returns (start, end) or None.

    Searches right-to-left for '(' that is preceded by a function name.
    Skips bare parentheses from tuple/group literals like (0,).
    """
    pos = len(expr)
    while True:
        pos = expr.rfind('(', 0, pos)
        if pos == -1:
            return None
        # Walk back to find the function name
        i = pos
        while i > 0 and (expr[i - 1].isalpha() or expr[i - 1] == '_'):
            i -= 1
        # Must have a function name - skip bare parens
        if i == pos:
            continue
        close = expr.find(')', pos)
        if close == -1:
            continue
        return i, close + 1


def is_safe_literal(s):
    """Can this repr be pasted back into an expression without confusing the parser?

    Must be eval-able AND not contain parens (which would look like function calls).
    """
    if '(' in s or ')' in s:
        return False
    try:
        eval(s, {"__builtins__": {}}, {})
        return True
    except Exception:
        return False


def evaluate_string_steps(text):
    """Evaluate a string expression in parallel per-character tracks.

    Returns a dict with:
      - wrapper: the outer eval(bytes(map(ord,next(zip(...))))) template
      - chars: list of {byte, label, steps} where steps are from evaluate_steps
    """
    from core.anchors import build_n

    repr_bytes = repr(text).encode('utf-8')
    tracks = []
    for b in repr_bytes:
        expr = f'chr({build_n(b)})'
        steps = evaluate_steps(expr)
        tracks.append({
            'byte': b,
            'label': chr(b) if 32 <= b < 127 else f'0x{b:02x}',
            'expr': expr,
            'steps': steps,
        })

    return {
        'text': text,
        'wrapper': 'eval(bytes(map(ord,next(zip(...)))))',
        'tracks': tracks,
    }


def truncate_repr(s, max_len=60):
    """Truncate long literals like lists, bytes, and strings for display."""
    if len(s) <= max_len:
        return s
    return s[:20] + ' \u2026 ' + s[-5:]


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
            s = s.replace(name, truncate_repr(repr(scope[name])))
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
            'result': truncate_repr(result_repr),
        })

        if is_safe_literal(result_repr) and len(result_repr) <= 30:
            current = current[:start] + result_repr + current[end:]
        else:
            current = current[:start] + make_placeholder(result) + current[end:]

    steps.append({'expr': resolve(current), 'final': True})
    return steps
