"""Export strategy breakdown from SQLite to static/database_stats.js"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
from db import get_conn, init_db

init_db()
conn = get_conn()

rows = conn.execute('''
    SELECT strategy, COUNT(*), ROUND(AVG(depth), 1)
    FROM numbers GROUP BY strategy ORDER BY COUNT(*) DESC
''').fetchall()
conn.close()

strategies = [{'name': r[0], 'count': r[1], 'avg_depth': r[2]} for r in rows]

output = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'database_stats.js')
with open(output, 'w') as f:
    f.write(f'const STRATEGY_BREAKDOWN = {json.dumps(strategies)};\n')

print(f"Exported {len(strategies)} strategies to static/database_stats.js")
