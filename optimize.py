"""Run improvement passes over the expressions database.

Tries every applicable strategy on every number and updates the db
when a shorter expression is found.
"""

import math
from db import get_conn, apply_strategy, snapshot, stats, init_db, MAX_N


MAX_OFFSET = 2


# ── Inverse functions ────────────────────────────────────────────────
# Given a target number, each returns (parent, offset) or None.

def inverse_linear(target, multiplier, constant):
    """Invert target = multiplier * parent - offset + constant."""
    for offset in range(MAX_OFFSET + 1):
        numerator = target + offset - constant
        if numerator > 0 and numerator % multiplier == 0:
            parent = numerator // multiplier
            if parent >= 1:
                return parent, offset
    return None


def inverse_triangular(target):
    """Invert target = parent * (parent - 1) / 2 - offset."""
    for offset in range(MAX_OFFSET + 1):
        val = target + offset
        disc = 1 + 8 * val
        sqrt_disc = math.isqrt(disc)
        if sqrt_disc * sqrt_disc == disc and (1 + sqrt_disc) % 2 == 0:
            parent = (1 + sqrt_disc) // 2
            if parent >= 2 and parent * (parent - 1) // 2 == val:
                return parent, offset
    return None


def inverse_enum_list(target):
    """Invert target = 8 * parent - offset (only for parent <= 10)."""
    for offset in range(MAX_OFFSET + 1):
        val = target + offset
        if val > 0 and val % 8 == 0:
            parent = val // 8
            if 1 <= parent <= 10:
                return parent, offset
    return None


def inverse_digit_offset(target, base_len):
    """Invert target = digits(parent) + base_len - offset, using smallest parent with d digits."""
    for offset in range(MAX_OFFSET + 1):
        d = target + offset - base_len
        if d < 1 or d > 6:
            continue
        parent = 1 if d == 1 else 10 ** (d - 1)
        if len(str(parent)) == d:
            return parent, offset
    return None


def inverse_slice(target):
    """Invert len(str(slice(n))) = digits(n) + 19."""
    result = inverse_digit_offset(target, 19)
    if result and len(str(slice(result[0]))) == target:
        return result
    return None


def inverse_complex(target):
    """Invert len(str(complex(n))) = digits(n) + 5."""
    result = inverse_digit_offset(target, 5)
    if result is None:
        return None
    try:
        if len(str(complex(result[0]))) == target:
            return result
    except (OverflowError, ValueError):
        pass
    return None


# ── Strategy table ───────────────────────────────────────────────────

def build_strategies():
    strategies = [
        ('triple',         lambda t: inverse_linear(t, 3, 0)),
        ('quad_plus_3',    lambda t: inverse_linear(t, 4, 3)),
        ('quint_plus_5',   lambda t: inverse_linear(t, 5, 5)),
        ('triangular',     inverse_triangular),
        ('enum_list_8x',   inverse_enum_list),
        ('slice_offset',   inverse_slice),
        ('complex_offset', inverse_complex),
    ]

    for k in range(1, 6):
        mult = 3 * (k + 1)
        strategies.append((f'zip_chain_{k}', lambda t, m=mult: inverse_linear(t, m, 0)))

    for k in range(1, 12):
        mult = (1 << k) + 3
        const = (1 << (k + 1)) + 1
        strategies.append((f'ascii_exp_{k}', lambda t, m=mult, c=const: inverse_linear(t, m, c)))

    return strategies


STRATEGIES = build_strategies()


# ── Optimization pass ────────────────────────────────────────────────

def load_entries():
    conn = get_conn()
    rows = conn.execute('SELECT n, expr, depth, len FROM numbers').fetchall()
    conn.close()
    return {n: {'expr': expr, 'depth': depth, 'len': length} for n, expr, depth, length in rows}


def find_improvements(entries, max_n):
    improvements = []

    for target in range(max_n + 1):
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

            try:
                candidate = apply_strategy(strategy_name, entries[parent_n]['expr'], offset)
            except ValueError:
                continue

            depth = candidate.count('(')
            if depth >= 200 or depth >= current['depth']:
                continue

            length = len(candidate)
            entries[target] = {'expr': candidate, 'depth': depth, 'len': length}
            current = entries[target]
            improvements.append((candidate, depth, length, strategy_name, parent_n, offset, target))

    return improvements


def write_improvements(improvements):
    if not improvements:
        return
    conn = get_conn()
    conn.executemany(
        'UPDATE numbers SET expr=?, depth=?, len=?, strategy=?, parent=?, offset=? WHERE n=?',
        improvements,
    )
    conn.commit()
    conn.close()


def run_pass(max_n=MAX_N):
    entries = load_entries()
    improvements = find_improvements(entries, max_n)
    write_improvements(improvements)
    return len(improvements)


if __name__ == '__main__':
    init_db()
    print("Running optimization pass...")
    n = run_pass()
    print(f"Improved {n} entries.")
    snapshot(f'optimization pass (+{n})', improvements=n)
    print()
    stats()
