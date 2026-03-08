"""Compute stats for all formula variants and print a comparison table.

Run this anytime to regenerate the numbers for the optimization history.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from anchors import build_n, BASE_ANCHORS
from db import get_conn

SAMPLE = list(range(0, 200_001, 10))


def _stats(depths):
    return {
        'avg': round(sum(depths) / len(depths), 1),
        'max': max(depths),
    }


def minimal_formula():
    """Base-3 with only seeds 0 and 1."""
    memo = {}
    def build(n):
        if n in memo: return memo[n]
        if n == 0: memo[0] = 'int(not(not()))'; return memo[0]
        if n == 1: memo[1] = 'int(not())'; return memo[1]
        q = -(-n // 3); r = 3 * q - n
        expr = f'len(str(list(bytes({build(q)}))))'
        for _ in range(r): expr = f'max(range({expr}))'
        memo[n] = expr; return expr
    return _stats([build(n).count('(') for n in SAMPLE])


def full_formula():
    """Base-3 with 44 base anchors."""
    return _stats([build_n(n).count('(') for n in SAMPLE])


def db_stats():
    """Current database (after optimization)."""
    conn = get_conn()
    row = conn.execute('SELECT AVG(depth), MAX(depth) FROM numbers').fetchone()
    conn.close()
    return {'avg': round(row[0], 1), 'max': row[1]} if row[0] else None


if __name__ == '__main__':
    print(f"{'Stage':<40} {'Avg depth':>10} {'Max depth':>10}")
    print('-' * 62)

    s = minimal_formula()
    print(f"{'minimal formula (seeds: 0, 1)':<40} {s['avg']:>10} {s['max']:>10}")

    s = full_formula()
    print(f"{'full formula (44 base anchors)':<40} {s['avg']:>10} {s['max']:>10}")

    s = db_stats()
    if s:
        print(f"{'database (optimized)':<40} {s['avg']:>10} {s['max']:>10}")
    else:
        print(f"{'database':<40} {'(no db)':>10}")
