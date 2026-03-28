"""Export all stats from SQLite to static/database_stats.js"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
from core.db import get_conn, init_db
from core.anchors import build_n

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'data')

init_db()
conn = get_conn()

# Strategy breakdown
strategy_rows = conn.execute('''
    SELECT strategy, COUNT(*), ROUND(AVG(depth), 1)
    FROM numbers GROUP BY strategy ORDER BY COUNT(*) DESC
''').fetchall()
strategies = [{'name': r[0], 'count': r[1], 'avg_depth': r[2]} for r in strategy_rows]

# Database stats
total, avg_depth, max_depth, avg_len, max_len = conn.execute('''
    SELECT COUNT(*), ROUND(AVG(depth), 2), MAX(depth), ROUND(AVG(len), 1), MAX(len)
    FROM numbers
''').fetchone()
db_stats = {
    'total': total,
    'avg_depth': avg_depth,
    'max_depth': max_depth,
    'avg_len': avg_len,
    'max_len': max_len,
}

# Optimization history — pick canonical entries by phase, preferring the most precise (latest) run
history_rows = conn.execute('''
    SELECT label, avg_depth, max_depth, avg_len FROM optimization_log ORDER BY id
''').fetchall()
conn.close()

# Map labels to canonical phase names, keep last occurrence of each phase
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
}

seen = {}
for label, avg_d, max_d, avg_l in history_rows:
    phase = next((v for k, v in PHASE_MAP.items() if label.startswith(k)), label)
    seen[phase] = {'label': phase, 'avg_depth': round(avg_d, 4), 'max_depth': max_d, 'avg_len': round(avg_l, 4)}

ORDER = [
    'minimal formula (seeds: 0, 1)',
    'full formula (44 base anchors)',
    'iterative optimizer',
    'deep search (offset \u2264 10)',
    'dijkstra (depth)',
    'dijkstra (length)',
]
history = [seen[p] for p in ORDER if p in seen]

# Formula stats (base-3 algorithm, no optimizations)
sample = list(range(0, 200_001, 10))
depths = []
lengths = []
for n in sample:
    expr = f'chr({build_n(n)})'
    depths.append(expr.count('('))
    lengths.append(len(expr))
formula_stats = {
    'sample_size': len(sample),
    'avg_depth': round(sum(depths) / len(depths), 1),
    'max_depth': max(depths),
    'avg_len': round(sum(lengths) / len(lengths), 1),
    'max_len': max(lengths),
}

output = os.path.join(STATIC_DIR, 'database_stats.js')
with open(output, 'w') as f:
    f.write(f'const STRATEGY_BREAKDOWN = {json.dumps(strategies)};\n')
    f.write(f'const DB_STATS = {json.dumps(db_stats)};\n')
    f.write(f'const FORMULA_STATS = {json.dumps(formula_stats)};\n')

history_output = os.path.join(STATIC_DIR, 'history.js')
with open(history_output, 'w') as f:
    f.write(f'const OPTIMIZATION_HISTORY = {json.dumps(history, indent=2)};\n')

print(f"Exported {len(strategies)} strategies, db stats, formula stats → database_stats.js")
print(f"Exported {len(history)} history entries → history.js")
