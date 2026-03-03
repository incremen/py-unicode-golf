"""Run improvement passes over the expressions database.

Tries every applicable strategy on every number and updates the db
when a shorter expression is found. Cascades improvements automatically.
"""

import math
from db import get, get_conn, improve, stats, init_db, _upsert

# ── Strategies ───────────────────────────────────────────────────────────
# Each strategy is: (name, input_fn, cost_fn)
#   - name: strategy identifier stored in db
#   - input_fn(target) → (parent_n, offset) or None if not applicable
#   - cost_fn: not needed, we just compute depth from the expression

# For a strategy that maps parent → result:
#   triple:      parent → 3*parent        (so parent = ceil(target/3), offset = 3*parent - target)
#   quad_plus_3: parent → 4*parent + 3    (so parent = ceil((target-3)/4), offset = 4*parent+3 - target)
#   quint_plus_5: parent → 5*parent + 5   (so parent = ceil((target-5)/5), offset = 5*parent+5 - target)
#   ascii_exp_k: parent → (2^k+3)*parent + (2^(k+1)+1)
#   zip_chain_k: parent → 3*(k+1)*parent
#   triangular:  parent → parent*(parent-1)/2

MAX_OFFSET = 2  # max decrements we'll try (to keep expressions short)


def _inverse_linear(target, multiplier, constant, max_offset=MAX_OFFSET):
    """For f(n) = multiplier*n + constant, find (parent, offset) to reach target.

    Returns (parent, offset) where f(parent) - offset = target,
    or None if offset would exceed max_offset.
    """
    # We need multiplier*parent + constant - offset = target
    # So multiplier*parent = target + offset - constant
    # Try offset = 0, 1, 2
    for offset in range(max_offset + 1):
        numerator = target + offset - constant
        if numerator <= 0:
            continue
        if numerator % multiplier == 0:
            parent = numerator // multiplier
            if parent >= 1:
                return parent, offset
    return None


def _inverse_triangular(target, max_offset=MAX_OFFSET):
    """For f(n) = n*(n-1)/2, find (parent, offset) to reach target."""
    for offset in range(max_offset + 1):
        val = target + offset
        # n*(n-1)/2 = val  →  n = (1 + sqrt(1 + 8*val)) / 2
        disc = 1 + 8 * val
        sqrt_disc = int(math.isqrt(disc))
        if sqrt_disc * sqrt_disc == disc and (1 + sqrt_disc) % 2 == 0:
            parent = (1 + sqrt_disc) // 2
            if parent >= 2 and parent * (parent - 1) // 2 == val:
                return parent, offset
    return None


STRATEGIES = []


def _register_strategies():
    global STRATEGIES

    # triple: f(n) = 3n
    STRATEGIES.append(('triple', lambda t: _inverse_linear(t, 3, 0)))

    # quad_plus_3: f(n) = 4n + 3
    STRATEGIES.append(('quad_plus_3', lambda t: _inverse_linear(t, 4, 3)))

    # quint_plus_5: f(n) = 5n + 5
    STRATEGIES.append(('quint_plus_5', lambda t: _inverse_linear(t, 5, 5)))

    # zip chains: f(n) = 3*(k+1)*n
    for k in range(1, 6):
        mult = 3 * (k + 1)
        name = f'zip_chain_{k}'
        STRATEGIES.append((name, lambda t, m=mult: _inverse_linear(t, m, 0)))

    # ascii exponential: f(n) = (2^k + 3)*n + (2^(k+1) + 1)
    for k in range(1, 12):
        mult = (1 << k) + 3
        const = (1 << (k + 1)) + 1
        name = f'ascii_exp_{k}'
        STRATEGIES.append((name, lambda t, m=mult, c=const: _inverse_linear(t, m, c)))

    # triangular: f(n) = n*(n-1)/2
    STRATEGIES.append(('triangular', _inverse_triangular))


_register_strategies()


# ── Optimization pass ────────────────────────────────────────────────────

def run_pass(max_n=155_000, verbose=True):
    """Try all strategies on all numbers. Returns count of improvements.

    Loads everything into memory for speed, then writes back improvements.
    """
    from db import _apply_strategy

    # Load entire db into memory
    conn = get_conn()
    rows = conn.execute('SELECT n, expr, depth, strategy, parent, offset FROM numbers').fetchall()
    conn.close()

    entries = {}  # n → {expr, depth, strategy, parent, offset}
    for n, expr, depth, strategy, parent, offset in rows:
        entries[n] = {
            'expr': expr, 'depth': depth,
            'strategy': strategy, 'parent': parent, 'offset': offset,
        }

    improvements = 0
    to_write = []  # (n, expr, depth, strategy, parent, offset)

    for target in range(0, max_n + 1):
        current_depth = entries[target]['depth'] if target in entries else float('inf')

        for strategy_name, inverse_fn in STRATEGIES:
            result = inverse_fn(target)
            if result is None:
                continue

            parent_n, offset = result
            if parent_n not in entries:
                continue

            parent_expr = entries[parent_n]['expr']

            try:
                candidate = _apply_strategy(strategy_name, parent_expr, offset)
            except (ValueError, KeyError):
                continue

            candidate_depth = candidate.count('(')
            if candidate_depth >= 200 or candidate_depth >= current_depth:
                continue

            # Found an improvement
            entries[target] = {
                'expr': candidate, 'depth': candidate_depth,
                'strategy': strategy_name, 'parent': parent_n, 'offset': offset,
            }
            current_depth = candidate_depth
            to_write.append((target, candidate, candidate_depth, strategy_name, parent_n, offset))
            improvements += 1

            if verbose and improvements <= 20:
                print(f"  improved {target}: → depth {candidate_depth} via {strategy_name}(parent={parent_n}, offset={offset})")

    # Write improvements back to db
    if to_write:
        conn = get_conn()
        conn.executemany('''
            INSERT INTO numbers (n, expr, depth, strategy, parent, offset)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(n) DO UPDATE SET
                expr=excluded.expr, depth=excluded.depth,
                strategy=excluded.strategy, parent=excluded.parent,
                offset=excluded.offset
        ''', to_write)
        conn.commit()
        conn.close()

    return improvements


# ── CLI ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    print("Running optimization pass...")
    n_improved = run_pass()
    print(f"\nImproved {n_improved} entries.")
    print()
    stats()
