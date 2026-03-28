"""Dijkstra-based optimizer for py-unicode-golf.

Builds the entire 0..MAX_N integer graph from BASE_ANCHORS using a
forward-search shortest-path algorithm, then bulk-writes to SQLite.

Usage:
    python scripts/optimize.py [--metric depth|length]
"""

import sys, os, heapq
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.anchors import BASE_ANCHORS
from core.db import init_db, snapshot, stats, bulk_write, MAX_N
from core.strategies import apply_strategy


# ── Configuration ─────────────────────────────────────────────────────────

METRIC      = 'depth'   # 'depth' or 'length'
PAREN_LIMIT = 200


# ── Forward strategy table ────────────────────────────────────────────────

def build_forward_strategies():
    strategies_list = [
        ('decrement',      lambda n: n - 1),
        ('triple',         lambda n: 3 * n),
        ('quad_plus_3',    lambda n: 4 * n + 3),
        ('quint_plus_5',   lambda n: 5 * n + 5),
        ('triangular',     lambda n: n * (n - 1) // 2),
        ('enum_list_8x',   lambda n: 8 * n if 1 <= n <= 10 else -1),
        ('slice_offset',   lambda n: len(str(n)) + 19 if n > 0 else -1),
        ('complex_offset', lambda n: len(str(n)) + 5  if n > 0 else -1),
    ]
    for k in range(1, 6):
        strategies_list.append((f'zip_chain_{k}', lambda n, m=3*(k+1): m * n))
    for k in range(1, 12):
        strategies_list.append((f'ascii_exp_{k}', lambda n, m=(1<<k)+3, c=(1<<(k+1))+1: m * n + c))
    return strategies_list

STRATEGIES = build_forward_strategies()


# ── Path tracker ──────────────────────────────────────────────────────────

class PathTracker:
    def __init__(self, metric='depth'):
        self.metric = metric
        self.priority_queue       = []
        self.best_primary_cost    = {}
        self.best_secondary_cost  = {}
        self.graph_nodes          = {}

    def add_path(self, target_number, expression_string, strategy_name='base', parent_number=None, decrement_count=0):
        depth  = expression_string.count('(')
        length = len(expression_string)
        p, s   = (depth, length) if self.metric == 'depth' else (length, depth)

        cur_p = self.best_primary_cost.get(target_number, float('inf'))
        cur_s = self.best_secondary_cost.get(target_number, float('inf'))

        if p < cur_p or (p == cur_p and s < cur_s):
            self.best_primary_cost[target_number]   = p
            self.best_secondary_cost[target_number] = s
            self.graph_nodes[target_number] = {
                'expr': expression_string, 'depth': depth, 'len': length,
                'strategy': strategy_name, 'parent': parent_number, 'offset': decrement_count,
            }
            heapq.heappush(self.priority_queue, (p, s, target_number))

    def pop_best_unexplored_node(self):
        while self.priority_queue:
            p, s, n = heapq.heappop(self.priority_queue)
            if (p <= self.best_primary_cost.get(n, float('inf')) and
                    s <= self.best_secondary_cost.get(n, float('inf'))):
                node = self.graph_nodes[n]
                return n, node['expr'], node['depth']
        return None, None, None


# ── Dijkstra ──────────────────────────────────────────────────────────────

def run_dijkstra():
    tracker = PathTracker(metric=METRIC)

    for anchor_value, anchor_expression in BASE_ANCHORS.items():
        tracker.add_path(anchor_value, anchor_expression)

    while True:
        source_number, source_expression, source_depth = tracker.pop_best_unexplored_node()
        if source_number is None:
            break

        for strategy_name, forward_fn in STRATEGIES:
            target_number = forward_fn(source_number)

            if not (0 <= target_number <= MAX_N):
                continue

            # Lower-bound depth pruning: every strategy adds ≥ 2 parens
            if source_depth + 2 >= tracker.best_primary_cost.get(target_number, float('inf')):
                continue

            try:
                target_expression = apply_strategy(strategy_name, source_expression, offset=0)
                if target_expression.count('(') >= PAREN_LIMIT:
                    continue
                tracker.add_path(
                    target_number=target_number,
                    expression_string=target_expression,
                    strategy_name=strategy_name,
                    parent_number=source_number,
                    decrement_count=1 if strategy_name == 'decrement' else 0,
                )
            except ValueError:
                pass

    return tracker.graph_nodes


# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if '--metric' in sys.argv:
        METRIC = sys.argv[sys.argv.index('--metric') + 1]
    assert METRIC in ('depth', 'length'), f'Unknown metric: {METRIC}'

    init_db()
    print(f'Running Dijkstra graph search (metric={METRIC})...')
    t0 = datetime.now()

    final_graph = run_dijkstra()

    elapsed = (datetime.now() - t0).total_seconds()
    print(f'Search completed in {elapsed:.1f}s. Found paths for {len(final_graph):,} numbers.')

    print('Writing graph to database...')
    written = bulk_write(final_graph)
    print(f'Inserted {written:,} rows.')

    snapshot(f'dijkstra (metric={METRIC})', improvements=written)
    stats()
