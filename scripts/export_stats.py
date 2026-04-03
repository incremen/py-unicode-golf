"""Export DB stats to static/data/*.js (database_stats.js and history.js).

CLI:
    python scripts/export_stats.py
"""

import os

import json
from core.db import get_conn, init_db
from core.anchors import build_n

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'data')

PHASE_MAP = {
    'minimal formula (seeds: 0, 1)':         'minimal formula (seeds: 0, 1)',
    'full formula (44 base anchors)':         'full formula (44 base anchors)',
    'base-3 (44 anchors)':                   'full formula (44 base anchors)',
    'optimizer (offset \u2264 2)':            'iterative optimizer',
    'iterative optimizer (offset \u2264 2)':  'iterative optimizer',
    'iterative pass':                         'iterative optimizer',
    'deep search (offset \u2264 10)':         'deep search (offset \u2264 10)',
    'iterative optimizer (offset \u2264 10)': 'deep search (offset \u2264 10)',
    'dijkstra (metric=depth)':               'dijkstra (depth)',
    'dijkstra (depth)':                      'dijkstra (depth)',
    'dijkstra (metric=length)':              'dijkstra (length)',
    'new strategies (depth)':               'new strategies (depth)',
    'new strategies (length)':              'new strategies (length)',
    'new strategies discovered':            'new strategies (depth)',
}

HISTORY_ORDER = [
    'minimal formula (seeds: 0, 1)',
    'full formula (44 base anchors)',
    'iterative optimizer',
    'deep search (offset \u2264 10)',
    'dijkstra (depth)',
    'dijkstra (length)',
    'new strategies (depth)',
    'new strategies (length)',
]


def export():
    init_db()
    conn = get_conn()

    # Strategy breakdown — final count + chain stats
    strategy_rows = conn.execute('''
        SELECT strategy, COUNT(*), ROUND(AVG(depth), 1)
        FROM numbers GROUP BY strategy ORDER BY COUNT(*) DESC
    ''').fetchall()

    # Walk every node's parent chain to count chain_entries and total_uses per strategy
    from collections import Counter
    all_nodes = {r[0]: (r[1], r[2]) for r in conn.execute('SELECT n, strategy, parent FROM numbers').fetchall()}
    chain_entries = Counter()
    total_uses    = Counter()
    for n, (strat, parent) in all_nodes.items():
        seen = set()
        cur = n
        while cur is not None:
            s, p = all_nodes.get(cur, (None, None))
            if s is None:
                break
            total_uses[s] += 1
            seen.add(s)
            cur = p
        for s in seen:
            chain_entries[s] += 1

    strategies = [{'name': r[0], 'count': r[1], 'avg_depth': r[2],
                   'chain_entries': chain_entries[r[0]],
                   'total_uses': total_uses[r[0]]}
                  for r in strategy_rows]

    # Database stats
    total, avg_depth, max_depth, avg_len, max_len = conn.execute('''
        SELECT COUNT(*), ROUND(AVG(depth), 2), MAX(depth), ROUND(AVG(len), 1), MAX(len)
        FROM numbers
    ''').fetchone()
    db_stats = {
        'total': total, 'avg_depth': avg_depth, 'max_depth': max_depth,
        'avg_len': avg_len, 'max_len': max_len,
    }

    # Optimization history — deduplicated by phase, last run wins
    history_rows = conn.execute(
        'SELECT label, avg_depth, max_depth, avg_len, max_len FROM optimization_log ORDER BY id'
    ).fetchall()
    conn.close()

    seen = {}
    for label, avg_d, max_d, avg_l, max_l in history_rows:
        phase = next((v for k, v in PHASE_MAP.items() if label.startswith(k)), label)
        seen[phase] = {'label': phase, 'avg_depth': round(avg_d, 4),
                       'max_depth': max_d, 'avg_len': round(avg_l, 4), 'max_len': max_l}
    history = [seen[p] for p in HISTORY_ORDER if p in seen]

    # Formula stats (base-3 algorithm, no optimizations, sampled)
    sample = list(range(0, 200_001, 10))
    depths  = [f'chr({build_n(n)})'.count('(') for n in sample]
    lengths = [len(f'chr({build_n(n)})')       for n in sample]
    formula_stats = {
        'sample_size': len(sample),
        'avg_depth': round(sum(depths)  / len(depths),  1),
        'max_depth': max(depths),
        'avg_len':   round(sum(lengths) / len(lengths), 1),
        'max_len':   max(lengths),
    }

    # Write files
    with open(os.path.join(STATIC_DIR, 'database_stats.js'), 'w') as f:
        f.write(f'const STRATEGY_BREAKDOWN = {json.dumps(strategies)};\n')
        f.write(f'const DB_STATS = {json.dumps(db_stats)};\n')
        f.write(f'const FORMULA_STATS = {json.dumps(formula_stats)};\n')

    with open(os.path.join(STATIC_DIR, 'history.js'), 'w') as f:
        f.write(f'const OPTIMIZATION_HISTORY = {json.dumps(history, indent=2)};\n')

    print(f"Exported {len(strategies)} strategies, db stats, formula stats → database_stats.js")
    print(f"Exported {len(history)} history entries → history.js")


if __name__ == '__main__':
    export()
