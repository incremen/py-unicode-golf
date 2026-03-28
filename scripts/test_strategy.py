"""Test new Dijkstra strategies without writing to the database.

Add candidate strategies to NEW_STRATEGIES below, then run.
Compares depth improvements against the current DB state.

CLI:
    python scripts/test_strategy.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.db import get_conn
from core.strategies import STRATEGIES
import scripts.optimize_dijksta as opt


# ┌─────────────────────────────────────────────────────────┐
# │  ADD YOUR STRATEGIES HERE                               │
# │                                                         │
# │  Same format as STRATEGIES in core/strategies.py:      │
# │  'name': (lambda n: <math>, lambda p: f'<expr>')       │
# └─────────────────────────────────────────────────────────┘

NEW_STRATEGIES = {
    # 'my_strategy': (lambda n: 6 * n + 1,
    #                 lambda p: f'len(str(list(zip(bytes({p})))))'),
}

# ┌─────────────────────────────────────────────────────────┐
# │  DON'T EDIT BELOW                                       │
# └─────────────────────────────────────────────────────────┘

if not NEW_STRATEGIES:
    print('No strategies defined. Add entries to NEW_STRATEGIES and re-run.')
    sys.exit(0)

conn = get_conn()
baseline = {r[0]: r[1] for r in conn.execute('SELECT n, depth FROM numbers').fetchall()}
conn.close()

STRATEGIES.update(NEW_STRATEGIES)
result = opt.run_dijkstra()
for name in NEW_STRATEGIES:
    del STRATEGIES[name]

improved = [(n, baseline[n], result[n]['depth']) for n in result if n in baseline and result[n]['depth'] < baseline[n]]
improved.sort(key=lambda x: x[1] - x[2], reverse=True)

print(f'Strategies tested: {list(NEW_STRATEGIES)}')
print(f'Improved: {len(improved):,} / {len(result):,} numbers')
if improved:
    print('Top improvements:')
    for n, old, new in improved[:20]:
        print(f'  n={n:>7}  depth {old} → {new}  (-{old - new})')
