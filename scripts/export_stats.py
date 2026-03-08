"""Export all stats from SQLite to static/database_stats.js"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
from db import get_conn, init_db
from anchors import build_n

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

conn.close()

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

print(f"Exported {len(strategies)} strategies, db stats, formula stats to static/database_stats.js")
