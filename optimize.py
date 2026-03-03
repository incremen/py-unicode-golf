"""Run improvement passes over the expressions database.

Tries every applicable strategy on every number and updates the db
when a shorter expression is found.
"""

import math
from db import get_conn, apply_strategy, snapshot, stats, init_db, MAX_N


# ── Strategy inverses ────────────────────────────────────────────────────
# Each: (name, inverse_fn) where inverse_fn(target) → (parent, offset) or None

MAX_OFFSET = 2

def _inverse_linear(target, multiplier, constant):
    for offset in range(MAX_OFFSET + 1):
        numerator = target + offset - constant
        if numerator <= 0:
            continue
        if numerator % multiplier == 0:
            parent = numerator // multiplier
            if parent >= 1:
                return parent, offset
    return None


def _inverse_triangular(target):
    for offset in range(MAX_OFFSET + 1):
        val = target + offset
        disc = 1 + 8 * val
        sqrt_disc = int(math.isqrt(disc))
        if sqrt_disc * sqrt_disc == disc and (1 + sqrt_disc) % 2 == 0:
            parent = (1 + sqrt_disc) // 2
            if parent >= 2 and parent * (parent - 1) // 2 == val:
                return parent, offset
    return None


STRATEGIES = []

# triple: 3n
STRATEGIES.append(('triple', lambda t: _inverse_linear(t, 3, 0)))

# quad_plus_3: 4n + 3
STRATEGIES.append(('quad_plus_3', lambda t: _inverse_linear(t, 4, 3)))

# quint_plus_5: 5n + 5
STRATEGIES.append(('quint_plus_5', lambda t: _inverse_linear(t, 5, 5)))

# zip chains: 3*(k+1)*n
for k in range(1, 6):
    mult = 3 * (k + 1)
    name = f'zip_chain_{k}'
    STRATEGIES.append((name, lambda t, m=mult: _inverse_linear(t, m, 0)))

# ascii exponential: (2^k + 3)*n + (2^(k+1) + 1)
for k in range(1, 12):
    mult = (1 << k) + 3
    const = (1 << (k + 1)) + 1
    name = f'ascii_exp_{k}'
    STRATEGIES.append((name, lambda t, m=mult, c=const: _inverse_linear(t, m, c)))

# triangular: n*(n-1)/2
STRATEGIES.append(('triangular', _inverse_triangular))


# ── Optimization pass ────────────────────────────────────────────────────

def run_pass(max_n=MAX_N, verbose=True):
    """Try all strategies on all numbers in memory, write back improvements."""
    conn = get_conn()
    rows = conn.execute('SELECT n, expr, depth, len FROM numbers').fetchall()
    conn.close()

    entries = {}
    for n, expr, depth, length in rows:
        entries[n] = {'expr': expr, 'depth': depth, 'len': length}

    improvements = 0
    to_write = []

    for target in range(0, max_n + 1):
        if target not in entries:
            continue
        current = entries[target]

        for strategy_name, inverse_fn in STRATEGIES:
            result = inverse_fn(target)
            if result is None:
                continue

            parent_n, offset = result
            if parent_n not in entries:
                continue

            parent_expr = entries[parent_n]['expr']

            try:
                candidate = apply_strategy(strategy_name, parent_expr, offset)
            except ValueError:
                continue

            depth = candidate.count('(')
            length = len(candidate)

            if depth >= 200 or depth >= current['depth']:
                continue

            entries[target] = {'expr': candidate, 'depth': depth, 'len': length}
            current = entries[target]
            to_write.append((candidate, depth, length, strategy_name, parent_n, offset, target))
            improvements += 1

    if to_write:
        conn = get_conn()
        conn.executemany('''
            UPDATE numbers SET expr=?, depth=?, len=?, strategy=?, parent=?, offset=?
            WHERE n=?
        ''', to_write)
        conn.commit()
        conn.close()

    return improvements


if __name__ == '__main__':
    init_db()
    print("Running optimization pass...")
    n = run_pass()
    print(f"Improved {n} entries.")
    snapshot(f'optimization pass (+{n})', improvements=n)
    print()
    stats()
